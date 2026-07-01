import sys
import os
import pandas as pd

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from cleansurvey.config import INPUT_DIR, FILES, AUX_DIR, OUTPUT_DIR, SAMPLE_FRACTION
from cleansurvey.utils import load_sav_data, apply_var_dictionary, apply_modality_dictionary

def main():
    print("--- DEBUT APPLICATION DICTIONNAIRE INDIVIDUS ---")
    dict_path = os.path.join(AUX_DIR, "dictionary_ind_filled.csv")
    init_path = os.path.join(AUX_DIR, "dictionary_ind_init.csv")
    
    if not os.path.exists(dict_path):
        if os.path.exists(init_path):
            print(f"Création automatique de {dict_path} à partir de {init_path}...")
            init_df = pd.read_csv(init_path)
            ind_mapping = {
                'men_id': 'men_id',
                'B01': 'numind',
                'B04': 'lien_parente',
                'B06': 'sexe',
                'B08': 'age',
                'B29': 'scolarisation',
                'B30': 'branche_etudes',
                'B32': 'niveau_etudes',
                'B41': 'situation_matrimoniale',
                'A01': 'region',
                'A02': 'departement',
                'A04': 'commune',
                'A10': 'milieu_residence',
                'B11': 'situation_residence',
                'B15B_REG': 'region_residence_1an',
                'B15B_DEP': 'dept_residence_1an',
                'B21': 'handicap_vision_brut',
                'B22': 'handicap_audition_brut',
                'B23': 'handicap_moteur_brut',
                'B24': 'handicap_cognitif_brut',
                'B25': 'handicap_soins_brut',
                'B26': 'handicap_communication_brut',
                'B36': 'statut_emploi',
                'B37': 'profession',
                'B39A': 'branche_isic',
                'B39B': 'secteur_instit',
                'B34_BRAILLE': 'alpha_br',
                'B34_FR': 'alpha_fr',
                'B34_WO': 'alpha_wo',
                'B34_ARABE': 'alpha_ar',
                'B34_PULAR': 'alpha_pu',
                'B34_SEREER': 'alpha_se',
                'B34_JOOLA': 'alpha_jo',
                'B34_MANDINKA': 'alpha_ma',
                'B34_SOONINKE': 'alpha_so',
                'B34_BASANIVA': 'alpha_ha',
                'B34_BALANT': 'alpha_ba',
                'B34_MANKAAN': 'alpha_mn',
                'B34_NOON': 'alpha_no',
                'B34_MANJAAK': 'alpha_mj',
                'B34_MENIK': 'alpha_me',
                'B34_ONIYAN': 'alpha_on',
                'B34_SAAFI_SAAFI': 'alpha_sa',
                'B34_GUNUNN': 'alpha_gu',
                'B34_LAALAA': 'alpha_la',
                'B34_KANJAD': 'alpha_ka',
                'B34_JALUNGA': 'alpha_ja',
                'B34_NDUT': 'alpha_nd',
                'B34_BAYOT': 'alpha_by',
                'B34_PALOOR': 'alpha_pa',
                'B34_WOMEY': 'alpha_wy'
            }
            init_df['var_new'] = init_df['var_orig'].map(ind_mapping).fillna(init_df['var_orig'])
            init_df['keep'] = init_df['var_orig'].apply(lambda x: 'yes' if x in ind_mapping else 'no')
            init_df.to_csv(dict_path, index=False, encoding='utf-8')
        else:
            print(f"Erreur : Le dictionnaire rempli {dict_path} et initial {init_path} sont introuvables.")
            sys.exit(1)
        
    # Lire le dictionnaire
    dict_df = pd.read_csv(dict_path)
    
    # Lire les données brutes
    raw_file = os.path.join(INPUT_DIR, FILES['ind'])
    keep_cols = dict_df[dict_df['keep'].str.lower() == 'yes']['var_orig'].tolist()
    
    df, meta = load_sav_data(raw_file, columns=keep_cols)
    
    # Échantillonnage si configuré
    if SAMPLE_FRACTION is not None and SAMPLE_FRACTION < 1.0:
        print(f"Échantillonnage de {SAMPLE_FRACTION*100}% de la base individus...")
        df = df.sample(frac=SAMPLE_FRACTION, random_state=42).copy()
        
    # Appliquer le dictionnaire de variables
    df_renamed = apply_var_dictionary(df, dict_df)
    
    # Sauvegarder les modalities initiales pour les facteurs
    mod_records = []
    for var_orig in keep_cols:
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
        mod_out_path = os.path.join(AUX_DIR, "dictionary_modality_ind_init.csv")
        df_mod.to_csv(mod_out_path, index=False, encoding='utf-8')
        print(f"✔ Dictionnaire de modalités initial sauvegardé dans : {mod_out_path}")
        
    # Appliquer directement le dictionnaire de modalités si disponible
    mod_filled_path = os.path.join(AUX_DIR, "dictionary_modality_ind_filled.csv")
    if not os.path.exists(mod_filled_path) and mod_records:
        print(f"Création de {mod_filled_path} à partir de la version init...")
        df_mod.to_csv(mod_filled_path, index=False, encoding='utf-8')
        
    if os.path.exists(mod_filled_path):
        print("Application des modalités sur la base individus...")
        dict_mod = pd.read_csv(mod_filled_path)
        df_renamed = apply_modality_dictionary(df_renamed, dict_mod)
        
    # Sauvegarder la base renommée et labellisée
    out_file = os.path.join(OUTPUT_DIR, "rgph5_ind_renamed.csv")
    df_renamed.to_csv(out_file, index=False, encoding='utf-8')
    print(f"✔ Base individus renommée et labellisée sauvegardée dans : {out_file}")

if __name__ == "__main__":
    main()
