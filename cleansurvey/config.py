"""
config.py
=========
Fichier de configuration central du pipeline RGPH - 10eme RGPH Senegal.

Pour adapter ce pipeline a un autre recensement contenant les memes modules,
modifier uniquement ce fichier : chemins, noms de variables brutes,
mappings de recodage, et regles de validation.
"""

import pathlib

# ==============================================================================
# 1. CHEMINS
# ==============================================================================
ROOT       = pathlib.Path(__file__).resolve().parent.parent
INPUT_DIR  = ROOT / "data"
OUTPUT_DIR = ROOT / "output"
DICT_DIR   = OUTPUT_DIR / "dict"
LOGS_DIR   = OUTPUT_DIR / "logs"

# Fichier source individus (Section B)
IND_SAV    = INPUT_DIR / "dixieme_RGPH_5_indiv_SECTION_B.sav"

# Fichiers de sortie
IND_CLEAN_CSV   = OUTPUT_DIR / "individus_clean.csv"
QAQC_XLSX       = OUTPUT_DIR / "QAQC_individus.xlsx"


# ==============================================================================
# 2. MAPPING VARIABLES BRUTES -> NOMS NORMALISES
#    Cle   : nom de la colonne dans le fichier .sav
#    Valeur : nom normalise dans la table de sortie
# ==============================================================================

IND_RENAME = {
    # -- Identifiants ----------------------------------------------------------
    "men_id"   : "id_menage",
    "B01"      : "num_ordre",          # Numero d'ordre dans le menage

    # -- Geographiques ---------------------------------------------------------
    "A01"      : "region",
    "A02"      : "departement",
    "A04"      : "commune",
    "A10"      : "milieu",

    # -- Demographiques --------------------------------------------------------
    "B04"      : "lien_cm",            # Lien de parente avec le CM
    "B06"      : "sexe",               # Sexe
    "B08"      : "age",                # Age (en annees revolues)
    "B07_A"    : "annee_naissance",    # Annee de naissance
    "B07_M"    : "mois_naissance",     # Mois de naissance
    "B07_J"    : "jour_naissance",     # Jour de naissance
    "B21"      : "situation_matrim",   # Situation matrimoniale
    "B32"      : "niveau_etudes",      # Niveau d'instruction (classe atteinte)
    "B33"      : "diplome",            # Diplome obtenu

    # -- Education -------------------------------------------------------------
    "B29"      : "scolarise",          # Frequentation scolaire (0=jamais, 1=avant, 2=actuellement)
    "B30"      : "type_enseignement",  # Type d'enseignement suivi

    # -- Alphabetisation (une colonne par langue) ------------------------------
    "B34_FR"        : "alpha_francais",
    "B34_WO"        : "alpha_wolof",
    "B34_ARABE"     : "alpha_arabe",
    "B34_PULAR"     : "alpha_pular",
    "B34_SEREER"    : "alpha_sereer",
    "B34_JOOLA"     : "alpha_joola",
    "B34_MANDINKA"  : "alpha_mandinka",
    "B34_SOONINKE"  : "alpha_sooninke",
    "B34_BASANIVA"  : "alpha_hasaniya",
    "B34_BALANT"    : "alpha_balant",
    "B34_MANKAAN"   : "alpha_mankaan",
    "B34_NOON"      : "alpha_noon",
    "B34_MANJAAK"   : "alpha_manjaak",
    "B34_MENIK"     : "alpha_menik",
    "B34_ONIYAN"    : "alpha_oniyan",
    "B34_SAAFI_SAAFI": "alpha_saafi_saafi",
    "B34_GUNUNN"    : "alpha_gununn",
    "B34_LAALAA"    : "alpha_laalaa",
    "B34_KANJAD"    : "alpha_kanjad",
    "B34_JALUNGA"   : "alpha_jalunga",
    "B34_NDUT"      : "alpha_ndut",
    "B34_BAYOT"     : "alpha_bayot",
    "B34_PALOOR"    : "alpha_paloor",
    "B34_WOMEY"     : "alpha_womey",
    "B34_BRAILLE"   : "alpha_braille",

    # -- Variables contextuelles (de la base, issues du traitement) ------------
    "Niv_Inst"      : "niveau_inst_recode",  # Niveau d'instruction recalcule
    "POIDS_STRATE_P": "poids_sondage",        # Poids de sondage
    "POP_TYPE"      : "type_population",
}

# -- Colonnes d'alphabetisation (toutes les variables alpha_*) -----------------
ALPHA_COLS_BRUTES = [
    "B34_FR", "B34_WO", "B34_ARABE", "B34_PULAR", "B34_SEREER",
    "B34_JOOLA", "B34_MANDINKA", "B34_SOONINKE", "B34_BASANIVA",
    "B34_BALANT", "B34_MANKAAN", "B34_NOON", "B34_MANJAAK",
    "B34_MENIK", "B34_ONIYAN", "B34_SAAFI_SAAFI", "B34_GUNUNN",
    "B34_LAALAA", "B34_KANJAD", "B34_JALUNGA", "B34_NDUT",
    "B34_BAYOT", "B34_PALOOR", "B34_WOMEY", "B34_BRAILLE",
]

# Noms normalises correspondants (meme ordre)
ALPHA_COLS_NORM = [
    "alpha_francais", "alpha_wolof", "alpha_arabe", "alpha_pular", "alpha_sereer",
    "alpha_joola", "alpha_mandinka", "alpha_sooninke", "alpha_hasaniya",
    "alpha_balant", "alpha_mankaan", "alpha_noon", "alpha_manjaak",
    "alpha_menik", "alpha_oniyan", "alpha_saafi_saafi", "alpha_gununn",
    "alpha_laalaa", "alpha_kanjad", "alpha_jalunga", "alpha_ndut",
    "alpha_bayot", "alpha_paloor", "alpha_womey", "alpha_braille",
]

# Code "Oui" dans les variables d'alphabetisation (valeur numerique brute)
ALPHA_OUI_CODE = 1.0


# ==============================================================================
# 3. MAPPINGS DE RECODAGE (modalites numeriques -> etiquettes textuelles)
# ==============================================================================

RECODE_SEXE = {
    1.0: "Masculin",
    2.0: "Feminin",
}

RECODE_MILIEU = {
    1.0: "Urbain",
    2.0: "Rural",
}

RECODE_LIEN_CM = {
    0.0 : "Sans lien de parente",
    1.0 : "Chef de menage",
    2.0 : "Epoux/Epouse",
    3.0 : "Fils/Fille",
    4.0 : "Frere/Soeur",
    5.0 : "Pere/Mere",
    6.0 : "Petit(e)s-fils/filles",
    7.0 : "Neveu/Niece",
    8.0 : "Oncle/Tante",
    9.0 : "Beau-fils/Belle-fille",
    10.0: "Autres parents",
    11.0: "Domestique",
}

RECODE_SITUATION_MATRIM = {
    1.0: "Celibataire",
    2.0: "Marie(e) monogame",
    3.0: "Marie(e) polygame 1ere epouse",
    4.0: "Marie(e) polygame autre epouse",
    5.0: "Union libre",
    6.0: "Divorce(e)/Separe(e)",
    7.0: "Veuf/Veuve",
}

# Niveau d'instruction : regroupement des classes en niveaux
# B32 contient la classe exacte (1=Petite section, 4=CI, ..., 24=8e annee+)
RECODE_NIVEAU_ETUDES_CLASSE = {
    # Prescolaire : 1-3
    1.0: "Prescolaire", 2.0: "Prescolaire", 3.0: "Prescolaire",
    # Primaire : 4-9 (CI a CM2)
    4.0: "Primaire", 5.0: "Primaire", 6.0: "Primaire",
    7.0: "Primaire", 8.0: "Primaire", 9.0: "Primaire",
    # Moyen : 10-13 (6e a 3e)
    10.0: "Moyen", 11.0: "Moyen", 12.0: "Moyen", 13.0: "Moyen",
    # Secondaire : 14-16 (Seconde, Premiere, Terminale)
    14.0: "Secondaire", 15.0: "Secondaire", 16.0: "Secondaire",
    # Superieur : 17+
    17.0: "Superieur", 18.0: "Superieur", 19.0: "Superieur",
    20.0: "Superieur", 21.0: "Superieur", 22.0: "Superieur",
    23.0: "Superieur", 24.0: "Superieur",
}

RECODE_SCOLARISE = {
    0.0: "Jamais scolarise",
    1.0: "Ancien eleve",
    2.0: "Actuellement scolarise",
}

RECODE_TYPE_ENSEIGNEMENT = {
    1.0: "Francais",
    2.0: "Franco-arabe",
    3.0: "Arabe pur",
    4.0: "Coranique",
    5.0: "Autre",
}

# Regroupement de tous les recodages
RECODINGS = {
    "sexe"             : RECODE_SEXE,
    "milieu"           : RECODE_MILIEU,
    "lien_cm"          : RECODE_LIEN_CM,
    "situation_matrim" : RECODE_SITUATION_MATRIM,
    "scolarise"        : RECODE_SCOLARISE,
    "type_enseignement": RECODE_TYPE_ENSEIGNEMENT,
}

# Recodage du niveau d'etudes (base sur la classe atteinte B32)
RECODE_NIVEAU_ETUDES = RECODE_NIVEAU_ETUDES_CLASSE


# ==============================================================================
# 4. REGLES DE VALIDATION
# ==============================================================================

# Plages de valeurs valides (min, max) pour les variables numeriques continues
VALID_RANGES = {
    "age"            : (0, 120),
    "annee_naissance": (1900, 2026),
}

# Valeurs considerees comme manquantes (en plus de NaN)
MISSING_CODES = {
    "age"             : [999.0, 99.0, 998.0],
    "annee_naissance" : [9999.0, 999.0],
    "mois_naissance"  : [99.0],
    "situation_matrim": [9.0, 99.0],
    "niveau_etudes"   : [99.0],
    "scolarise"       : [],          # Modalites deja codees 0/1/2 sans NSP
    "sexe"            : [9.0],
    "milieu"          : [9.0],
    "lien_cm"         : [99.0],
}

# Controles de coherence (expressions evaluables avec pandas DataFrame.eval)
COHERENCE_CHECKS = [
    {
        "nom"        : "age_scolarise",
        "description": "Enfants < 3 ans declares actuellement scolarises",
        "condition"  : "age < 3 and scolarise == 'Actuellement scolarise'",
    },
    {
        "nom"        : "age_matrim_enfant",
        "description": "Enfants < 10 ans declares maries ou en union",
        "condition"  : "age < 10 and situation_matrim not in ['Celibataire', 'Jamais scolarise']",
    },
    {
        "nom"        : "sexe_manquant",
        "description": "Sexe manquant",
        "condition"  : "sexe != sexe",  # NaN check
    },
    {
        "nom"        : "age_manquant",
        "description": "Age manquant",
        "condition"  : "age != age",    # NaN check
    },
]


# ==============================================================================
# 5. GROUPES D'AGE (pyramide des ages)
# ==============================================================================

AGE_BINS   = [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 200]
AGE_LABELS = [
    "0-4", "5-9", "10-14", "15-19", "20-24", "25-29",
    "30-34", "35-39", "40-44", "45-49", "50-54", "55-59",
    "60-64", "65-69", "70-74", "75-79", "80+",
]


# ==============================================================================
# 6. VARIABLES CATEGORIELLESS POUR LES DISTRIBUTIONS QAQC
# ==============================================================================

CAT_VARS_QAQC = [
    "sexe", "milieu", "region", "lien_cm",
    "situation_matrim", "niveau_etudes_groupe",
    "scolarise", "type_enseignement",
    "groupe_age", "alphabetise",
]
