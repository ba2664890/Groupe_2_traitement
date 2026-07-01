import sys
import os
import pandas as pd

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from cleansurvey.config import INPUT_DIR, FILES, AUX_DIR, OUTPUT_DIR
from cleansurvey.utils import load_sav_data, apply_var_dictionary, apply_modality_dictionary

def main():
    print("--- DEBUT APPLICATION DICTIONNAIRE MENAGES (HABITAT) ---")
    dict_path = os.path.join(AUX_DIR, "dictionary_hh_filled.csv")
    init_path = os.path.join(AUX_DIR, "dictionary_hh_init.csv")
    
    if not os.path.exists(dict_path):
        if os.path.exists(init_path):
            print(f"Création automatique de {dict_path} à partir de {init_path}...")
            init_df = pd.read_csv(init_path)
            hh_mapping = {
                'men_id': 'men_id',
                'A01': 'region',
                'A02': 'departement',
                'A04': 'commune',
                'A10': 'milieu_residence'
            }
            init_df['var_new'] = init_df['var_orig'].map(hh_mapping).fillna(init_df['var_orig'])
            init_df['keep'] = init_df['var_orig'].apply(lambda x: 'yes' if x in hh_mapping else 'no')
            init_df.to_csv(dict_path, index=False, encoding='utf-8')
        else:
            print(f"Erreur : Le dictionnaire rempli {dict_path} et initial {init_path} sont introuvables.")
            sys.exit(1)
        
    # Lire le dictionnaire
    dict_df = pd.read_csv(dict_path)
    
    # Lire les données brutes
    raw_file = os.path.join(INPUT_DIR, FILES['hh'])
    keep_cols = dict_df[dict_df['keep'].str.lower() == 'yes']['var_orig'].tolist()
    
    df, meta = load_sav_data(raw_file, columns=keep_cols)
    
    # Appliquer le dictionnaire de variables
    df_renamed = apply_var_dictionary(df, dict_df)
    
    # Sauvegarder les modalities initiales pour les facteurs
    mod_records = []
    for var_orig in keep_cols:
        # Trouver le nouveau nom correspondant
        var_new = dict_df[dict_df['var_orig'] == var_orig]['var_new'].values[0]
        if var_orig in meta.variable_value_labels:
            labels = meta.variable_value_labels[var_orig]
            for code, label in labels.items():
                mod_records.append({
                    "var_name": var_new,
                    "code": code,
                    "label_init": label,
                    "label_new": label # Par défaut, on garde la même étiquette
                })
                
    if mod_records:
        df_mod = pd.DataFrame(mod_records)
        mod_out_path = os.path.join(AUX_DIR, "dictionary_modality_hh_init.csv")
        df_mod.to_csv(mod_out_path, index=False, encoding='utf-8')
        print(f"✔ Dictionnaire de modalités initial sauvegardé dans : {mod_out_path}")
        
    # Appliquer directement le dictionnaire de modalités si disponible
    mod_filled_path = os.path.join(AUX_DIR, "dictionary_modality_hh_filled.csv")
    if not os.path.exists(mod_filled_path) and mod_records:
        print(f"Création de {mod_filled_path} à partir de la version init...")
        df_mod.to_csv(mod_filled_path, index=False, encoding='utf-8')
        
    if os.path.exists(mod_filled_path):
        print("Application des modalités sur la base ménages...")
        dict_mod = pd.read_csv(mod_filled_path)
        df_renamed = apply_modality_dictionary(df_renamed, dict_mod)
        
    # Sauvegarder la base renommée et labellisée
    out_file = os.path.join(OUTPUT_DIR, "rgph5_hh_renamed.csv")
    df_renamed.to_csv(out_file, index=False, encoding='utf-8')
    print(f"✔ Base ménages renommée et labellisée sauvegardée dans : {out_file}")

if __name__ == "__main__":
    main()
