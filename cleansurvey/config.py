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
        'age': [0, 120]
    },
    
    # Stratégie d'imputation numérique: "median" | "mean" | "zero" | "none"
    'numeric_impute': {
        'age': 'median'
    },
    
    # Stratégie d'imputation catégorielle: "mode" | "Unknown" | "none"
    'categ_impute': {
        'sexe': 'mode',
        'situation_matrimoniale': 'Unknown',
        'lien_parente': 'none',
        'region': 'mode',
        'departement': 'mode',
        'commune': 'mode',
        'milieu_residence': 'mode',
        'scolarisation': 'none',
        'niveau_etudes': 'none'
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

# Fraction d'échantillonnage pour accélérer les calculs (ex: 0.1 pour 10%)
SAMPLE_FRACTION = None

