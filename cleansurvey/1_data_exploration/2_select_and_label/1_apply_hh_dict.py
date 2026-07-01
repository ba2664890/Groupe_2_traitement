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
        
    # Charger la base individus renommée pour calculer la taille et extraire le CM
    ind_renamed_file = os.path.join(OUTPUT_DIR, "rgph5_ind_renamed.csv")
    if os.path.exists(ind_renamed_file):
        print(" Enrichissement de la base ménages avec la taille et les variables du CM...")
        df_ind = pd.read_csv(ind_renamed_file)
        
        # 1. Calcul de la taille du ménage
        df_taille = df_ind.groupby('men_id').size().reset_index(name='taille_menage')
        df_renamed = df_renamed.merge(df_taille, on='men_id', how='left')
        
        # 2. Extraction du Chef de Ménage (CM)
        # Trouver dynamiquement l'étiquette de Chef de Ménage (code 1.0) dans les métadonnées
        mod_filled_path = os.path.join(AUX_DIR, "dictionary_modality_ind_filled.csv")
        cm_label = "Chef de ménage"
        
        def load_mapping_from_dict(var_name):
            mapping = {}
            if os.path.exists(mod_filled_path):
                df_mod = pd.read_csv(mod_filled_path)
                df_var = df_mod[df_mod['var_name'] == var_name]
                for _, row in df_var.iterrows():
                    code = row['code']
                    lbl = row['label_new']
                    mapping[code] = lbl
                    mapping[str(code)] = lbl
                    try:
                        mapping[int(float(code))] = lbl
                        mapping[f"{float(code):.1f}"] = lbl
                    except ValueError:
                        pass
            return mapping
            
        parente_lbls = load_mapping_from_dict('lien_parente')
        for code, label in parente_lbls.items():
            if str(code) in ['1', '1.0'] or code == 1:
                cm_label = label
                break
                
        cm_mask = df_ind['lien_parente'].astype(str).str.strip().str.lower().isin([
            str(cm_label).strip().lower(), 'chef de ménage', 'chef de menage', '1', '1.0'
        ])
        df_cm = df_ind[cm_mask].copy()
        cm_cols = {
            'men_id': 'men_id',
            'sexe': 'sexe_cm',
            'age': 'age_cm',
            'scolarisation': 'scolarisation_cm',
            'niveau_etudes': 'niveau_etudes_cm',
            'situation_matrimoniale': 'situation_matrimoniale_cm',
            'statut_emploi': 'statut_emploi_cm',
            'branche_isic': 'branche_isic_cm',
            'secteur_instit': 'secteur_instit_cm'
        }
        cm_cols_keep = [c for c in cm_cols.keys() if c in df_cm.columns]
        df_cm = df_cm[cm_cols_keep].rename(columns={c: cm_cols[c] for c in cm_cols_keep})
        
        # Mappage dynamique des variables d'emploi/secteur pour le CM
        statut_emploi_lbl = load_mapping_from_dict('statut_emploi')
        secteur_instit_lbl = load_mapping_from_dict('secteur_instit')
        
        if 'statut_emploi_cm' in df_cm.columns and statut_emploi_lbl:
            df_cm['statut_emploi_cm'] = df_cm['statut_emploi_cm'].map(statut_emploi_lbl).fillna(df_cm['statut_emploi_cm'])
        if 'secteur_instit_cm' in df_cm.columns and secteur_instit_lbl:
            df_cm['secteur_instit_cm'] = df_cm['secteur_instit_cm'].map(secteur_instit_lbl).fillna(df_cm['secteur_instit_cm'])

        df_cm = df_cm.drop_duplicates(subset=['men_id'], keep='first')
        df_renamed = df_renamed.merge(df_cm, on='men_id', how='left')
    else:
        print(" Base individus renommée absente. Pas d'enrichissement de la base ménages.")
        
    # Sauvegarder la base renommée et labellisée
    out_file = os.path.join(OUTPUT_DIR, "rgph5_hh_renamed.csv")
    df_renamed.to_csv(out_file, index=False, encoding='utf-8')
    print(f" Base ménages renommée et labellisée sauvegardée dans : {out_file}")

if __name__ == "__main__":
    main()
