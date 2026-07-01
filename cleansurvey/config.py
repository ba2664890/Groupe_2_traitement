# Configuration du pipeline de traitement des données de recensement RGPH-5
import os

# 1. CHEMINS D'ACCÈS
INPUT_DIR = "/home/abdou/Documents/Memoire_AS/data/Base_1_10rgph-5"
OUTPUT_DIR = "/home/abdou/Documents/Groupe_2_traitement/data"
AUX_DIR = "/home/abdou/Documents/Groupe_2_traitement/data/aux_file"
QAQC_DIR = "/home/abdou/Documents/Groupe_2_traitement/data/output_qaqc"

# S'assurer que les dossiers de sortie existent
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(AUX_DIR, exist_ok=True)
os.makedirs(QAQC_DIR, exist_ok=True)

# 2. DEFINITION DES FICHIERS SOURCE
FILES = {
    'hh': 'dixieme_RGPH_5_habitat_SECTION_E.sav',
    'ind': 'dixieme_RGPH_5_indiv_SECTION_B.sav'
}

# 3. STRATÉGIE DE NETTOYAGE PARAMÉTRÉE
CLEANING_PARAMS = {
    # Bornes pour les variables numériques [min, max]
    'numeric_bounds': {
        'age': [0, 120],
        'age_cm': [0, 120],
        'taille_menage': [1, 125],
        'revenu_emploi_estime': [0, 5000000]
    },
    
    # Stratégie d'imputation numérique: "median" | "mean" | "zero" | "none"
    'numeric_impute': {
        'age': 'median',
        'age_cm': 'median',
        'taille_menage': 'median',
        'revenu_emploi_estime': 'zero'
    },
    
    # Stratégie d'imputation catégorielle: "mode" | "Unknown" | "none"
    'categ_impute': {
        'sexe': 'mode',
        'sexe_cm': 'mode',
        'situation_matrimoniale': 'Unknown',
        'situation_matrimoniale_cm': 'Unknown',
        'lien_parente': 'none',
        'region': 'mode',
        'departement': 'mode',
        'commune': 'mode',
        'milieu_residence': 'mode',
        'scolarisation': 'none',
        'niveau_etudes': 'none',
        'type_menage': 'mode',
        'statut_emploi_cm': 'Unknown',
        'secteur_instit_cm': 'Unknown',
        'branche_isic_cm': 'Unknown',
        'statut_emploi': 'mode',
        'secteur_instit': 'Unknown',
        'branche_isic': 'Unknown',
        'profession': 'Unknown',
        'situation_residence': 'mode',
        'region_residence_1an': 'Unknown',
        'dept_residence_1an': 'Unknown',
        'handicap_vision': 'none',
        'handicap_audition': 'none',
        'handicap_moteur': 'none',
        'handicap_cognitif': 'none',
        'handicap_soins': 'none',
        'handicap_communication': 'none'
    },
    
    # Règles de cohérence logique (cross-variable validation)
    # condition: expression évaluée en Python
    # target: la colonne à modifier si la condition est VRAIE
    # action: valeur par laquelle remplacer la valeur de la cible
    'consistency_rules': [
        {
            'label': 'Mariage précoce (age < 12 et non célibataire)',
            'condition': 'age < 12 and situation_matrimoniale != "Célibataire" and situation_matrimoniale.notna()',
            'target': 'situation_matrimoniale',
            'action': 'Célibataire'
        },
        {
            'label': 'Éducation précoce (age < 3 et scolarisation active)',
            'condition': 'age < 3 and scolarisation != "non, n\'a jamais fréquenté" and scolarisation.notna()',
            'target': 'scolarisation',
            'action': "non, n'a jamais fréquenté"
        },
        {
            'label': 'Niveau études précoce (age < 5 et niveau_etudes.notna())',
            'condition': 'age < 5 and niveau_etudes.notna()',
            'target': 'niveau_etudes',
            'action': 'na'
        },
        {
            'label': 'Cohérence Sexe et Epouse (sexe != "Féminin" et lien_parente == "Epouse (ou époux) du CM")',
            'condition': 'sexe != "Féminin" and lien_parente == "Epouse (ou époux) du CM"',
            'target': 'sexe',
            'action': 'Féminin'
        },
        {
            'label': 'CM masculin déclaré épouse (polygamie)',
            'condition': 'sexe_cm == "Masculin" and situation_matrimoniale_cm in ["Polygame – 1ère épouse", "Polygame – 2ème épouse", "Polygame – 3ème épouse", "Polygame – 4ème épouse", "Polygame – 5ème épouse ou +"]',
            'target': 'situation_matrimoniale_cm',
            'action': 'na'
        },
        {
            'label': 'Travail des enfants (age < 10 et occupé/chômeur)',
            'condition': 'age < 10 and statut_emploi in ["Occupé", "Chômeur ayant déjà travaillé"]',
            'target': 'statut_emploi',
            'action': 'Autres inactifs'
        },
        {
            'label': 'Profession enfant (age < 10 et profession renseignée)',
            'condition': 'age < 10 and profession.notna()',
            'target': 'profession',
            'action': 'na'
        },
        {
            'label': 'Secteur d\'activité pour non-actifs',
            'condition': 'statut_emploi not in ["Occupé", "Chômeur ayant déjà travaillé"] and secteur_instit.notna()',
            'target': 'secteur_instit',
            'action': 'na'
        },
        {
            'label': 'Revenu cohérent inactif (non occupé et revenu > 0)',
            'condition': 'statut_emploi not in ["Occupé", "Chômeur ayant déjà travaillé"] and revenu_emploi_estime > 0',
            'target': 'revenu_emploi_estime',
            'action': 0.0
        },
        {
            'label': 'Mariage précoce du CM (age_cm < 12 et non célibataire)',
            'condition': 'age_cm < 12 and situation_matrimoniale_cm != "Célibataire" and situation_matrimoniale_cm.notna()',
            'target': 'situation_matrimoniale_cm',
            'action': 'Célibataire'
        },
        {
            'label': 'Scolarisation précoce du CM (age_cm < 3 et scolarisé)',
            'condition': 'age_cm < 3 and scolarisation_cm != "non, n\'a jamais fréquenté" and scolarisation_cm.notna()',
            'target': 'scolarisation_cm',
            'action': "non, n'a jamais fréquenté"
        },
        {
            'label': 'Secteur d\'activité pour CM non-actif',
            'condition': 'statut_emploi_cm not in ["Occupé", "Chômeur ayant déjà travaillé"] and secteur_instit_cm.notna()',
            'target': 'secteur_instit_cm',
            'action': 'na'
        }
    ],
    
    # Stratégie de gestion des doublons de colonnes lors de la jointure
    # stratégie: "hh" (garder HH) | "ind" (garder IND) | "both" (garder les deux avec suffixes)
    'duplicate_cols_strategy': {
        'region': 'ind',
        'departement': 'ind',
        'commune': 'ind',
        'milieu_residence': 'ind'
    },
    
    'suffixes': ('_hh', '_ind')
}

# Codes de modalités spéciales à remplacer par NaN
NSP_CODES = [88.0, 99.0, 999.0, 9999.0, 888.0, 998.0]

# Clé de jointure composite pour les ménages
ID_KEY = ["A06", "A09"]

# Fraction d'échantillonnage pour accélérer les calculs (ex: 0.1 pour 10%)
SAMPLE_FRACTION = None

