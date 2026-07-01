"""
cleansurvey/1_data_exploration/2_select_and_label/2_2_apply_ind_dict.py
=====================================================================
Étape 3 - Application de la deuxième partie individus (Emploi, Handicap, Migration)
"""

import sys
import os
import pandas as pd
import numpy as np

# Ajouter le chemin racine du projet au path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from cleansurvey.config import AUX_DIR, OUTPUT_DIR

def load_mapping_from_dict(var_name):
    """
    Charge dynamiquement le dictionnaire de correspondance des modalités (code -> label)
    à partir du dictionnaire de modalités généré depuis les métadonnées du fichier .sav.
    """
    mod_filled_path = os.path.join(AUX_DIR, "dictionary_modality_ind_filled.csv")
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
                # Gérer le cas des codes numériques (int et float)
                mapping[int(float(code))] = lbl
                mapping[f"{float(code):.1f}"] = lbl
            except ValueError:
                pass
    return mapping

def dichotomiser_handicap(df, col_brut, col_nouveau):
    """
    Crée une variable dichotomique (1 = Oui, 0 = Non) pour le handicap.
    Oui si 'Beaucoup de difficultés' ou 'Ne peut pas du tout' (ou codes 3, 4).
    """
    if col_brut in df.columns:
        valeurs_oui = ['beaucoup de difficultés', 'ne peut pas du tout', '3', '4', '3.0', '4.0']
        df[col_nouveau] = df[col_brut].astype(str).str.strip().str.lower().isin(valeurs_oui).astype(int)
        # Si la colonne d'origine est NaN, on remet NaN
        df.loc[df[col_brut].isna(), col_nouveau] = np.nan
    return df

def estimer_revenu(row):
    """Estime le revenu individuel basé sur le statut et le secteur d'activité."""
    statut = str(row.get('statut_emploi', '')).strip().lower()
    # Si la personne n'est pas occupée (différent de 1 ou 'occupé'), le revenu est de 0
    if 'occupé' not in statut and statut not in ['1', '1.0']:
        return 0.0
        
    secteur = str(row.get('secteur_instit', '')).strip().lower()
    if 'public' in secteur or secteur in ['1', '1.0']:
        return 350000.0
    elif 'privé' in secteur or 'prive' in secteur or secteur in ['2', '2.0']:
        return 250000.0
    elif 'informel' in secteur or secteur in ['3', '3.0']:
        return 90000.0
    elif 'isblsm' in secteur or 'ong' in secteur or secteur in ['4', '4.0']:
        return 200000.0
    else:
        # Secteur occupé mais inconnu
        return 120000.0

def main():
    print("--- DEBUT APPLICATION DE LA DEUXIEME PARTIE INDIVIDUS ---")
    
    ind_renamed_file = os.path.join(OUTPUT_DIR, "rgph5_ind_renamed.csv")
    if not os.path.exists(ind_renamed_file):
        print(f"Erreur : La base individus renommée {ind_renamed_file} est introuvable.")
        sys.exit(1)
        
    df = pd.read_csv(ind_renamed_file)
    print(f"Base chargée : {len(df):,} lignes x {df.shape[1]} colonnes")
    
    # 1. Mappage dynamique des modalités à partir du dictionnaire de métadonnées .sav
    print("Chargement dynamique des modalités depuis le dictionnaire de métadonnées...")
    statut_emploi_lbl = load_mapping_from_dict('statut_emploi')
    secteur_instit_lbl = load_mapping_from_dict('secteur_instit')
    situation_residence_lbl = load_mapping_from_dict('situation_residence')
    handicap_lbl = load_mapping_from_dict('handicap_vision_brut') # Identique pour toutes les limitations
    
    print("Application du mappage des modalités...")
    if 'statut_emploi' in df.columns and statut_emploi_lbl:
        df['statut_emploi'] = df['statut_emploi'].map(statut_emploi_lbl).fillna(df['statut_emploi'])
        
    if 'secteur_instit' in df.columns and secteur_instit_lbl:
        df['secteur_instit'] = df['secteur_instit'].map(secteur_instit_lbl).fillna(df['secteur_instit'])
        
    if 'situation_residence' in df.columns and situation_residence_lbl:
        df['situation_residence'] = df['situation_residence'].map(situation_residence_lbl).fillna(df['situation_residence'])
        
    handicap_brut_cols = [
        'handicap_vision_brut', 'handicap_audition_brut', 'handicap_moteur_brut',
        'handicap_cognitif_brut', 'handicap_soins_brut', 'handicap_communication_brut'
    ]
    if handicap_lbl:
        for col in handicap_brut_cols:
            if col in df.columns:
                df[col] = df[col].map(handicap_lbl).fillna(df[col])
            
    # 2. Dichotomisation du handicap (Groupe de Washington)
    print("Génération des variables de handicap dichotomiques...")
    handicap_pairs = [
        ('handicap_vision_brut', 'handicap_vision'),
        ('handicap_audition_brut', 'handicap_audition'),
        ('handicap_moteur_brut', 'handicap_moteur'),
        ('handicap_cognitif_brut', 'handicap_cognitif'),
        ('handicap_soins_brut', 'handicap_soins'),
        ('handicap_communication_brut', 'handicap_communication')
    ]
    for col_brut, col_nouveau in handicap_pairs:
        df = dichotomiser_handicap(df, col_brut, col_nouveau)
        
    # 3. Simulation/Estimation du revenu lié à l'emploi
    print("Simulation du revenu de l'emploi estimé...")
    if 'statut_emploi' in df.columns and 'secteur_instit' in df.columns:
        df['revenu_emploi_estime'] = df.apply(estimer_revenu, axis=1)
    else:
        df['revenu_emploi_estime'] = 0.0
        
    # 4. Gestion rigoureuse des sauts de questionnaire (Skip Logic)
    print("Application rigoureuse de la logique de saut de questionnaire...")
    
    # 4.1. Sauts liés à la scolarisation (non scolarisés)
    if 'scolarisation' in df.columns:
        non_scol_mask = df['scolarisation'].astype(str).str.strip().str.lower().isin([
            "non, n'a jamais fréquenté", "non, n'a jamais fréquente", "non, n\'a jamais fréquenté", "non"
        ])
        if 'niveau_etudes' in df.columns:
            df.loc[non_scol_mask, 'niveau_etudes'] = 'na'
        if 'branche_etudes' in df.columns:
            df.loc[non_scol_mask, 'branche_etudes'] = 'na'
            
    # 4.2. Sauts liés à l'emploi (Inactifs)
    if 'statut_emploi' in df.columns:
        inact_vals = ['occupé', 'chômeur ayant déjà travaillé', 'occupé', 'chomeur ayant deja travaille', '1', '2', '1.0', '2.0']
        inactif_mask = ~df['statut_emploi'].astype(str).str.strip().str.lower().isin(inact_vals)
        if 'profession' in df.columns:
            df.loc[inactif_mask, 'profession'] = 'na'
        if 'secteur_instit' in df.columns:
            df.loc[inactif_mask, 'secteur_instit'] = 'na'
        if 'branche_isic' in df.columns:
            df.loc[inactif_mask, 'branche_isic'] = 'na'
        if 'revenu_emploi_estime' in df.columns:
            df.loc[inactif_mask, 'revenu_emploi_estime'] = 0.0
            
    # 4.3. Sauts liés à l'âge (enfants de moins de 5 ans)
    if 'age' in df.columns:
        moins5_mask = df['age'] < 5
        if 'scolarisation' in df.columns:
            df.loc[moins5_mask, 'scolarisation'] = "non, n'a jamais fréquenté"
        if 'niveau_etudes' in df.columns:
            df.loc[moins5_mask, 'niveau_etudes'] = 'na'
        if 'branche_etudes' in df.columns:
            df.loc[moins5_mask, 'branche_etudes'] = 'na'
            
        # Alphabétisation impossible pour moins de 5 ans
        alpha_cols = [c for c in df.columns if c.startswith('alpha_')]
        for col in alpha_cols:
            df.loc[moins5_mask, col] = 'na'
            
        # 4.4. Sauts liés à l'âge (enfants de moins de 10 ans pour l'emploi)
        moins10_mask = df['age'] < 10
        if 'statut_emploi' in df.columns:
            df.loc[moins10_mask, 'statut_emploi'] = 'Autres inactifs'
        if 'profession' in df.columns:
            df.loc[moins10_mask, 'profession'] = 'na'
        if 'secteur_instit' in df.columns:
            df.loc[moins10_mask, 'secteur_instit'] = 'na'
        if 'branche_isic' in df.columns:
            df.loc[moins10_mask, 'branche_isic'] = 'na'
        if 'revenu_emploi_estime' in df.columns:
            df.loc[moins10_mask, 'revenu_emploi_estime'] = 0.0
            
        # 4.5. Sauts liés à l'âge (enfants de moins de 1 an pour la résidence il y a 1 an)
        moins1_mask = df['age'] < 1
        if 'region_residence_1an' in df.columns:
            df.loc[moins1_mask, 'region_residence_1an'] = 'na'
        if 'dept_residence_1an' in df.columns:
            df.loc[moins1_mask, 'dept_residence_1an'] = 'na'
        
    # Sauvegarder la base mise à jour
    df.to_csv(ind_renamed_file, index=False, encoding='utf-8')
    print(f"✔ Base individus enrichie sauvegardée dans : {ind_renamed_file}")
    print(f"Structure finale : {df.shape[0]:,} lignes x {df.shape[1]} colonnes")

if __name__ == "__main__":
    main()
