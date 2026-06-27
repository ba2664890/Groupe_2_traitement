"""
config.py - Configuration centrale du pipeline Groupe 2
"""

from pathlib import Path
# On importe la classe Path de la bibliothèque standard Python.
# Path permet de construire des chemins de fichiers intelligemment,
# sans se soucier des différences Windows (\) ou Linux/Mac (/).

# -- DOSSIERS DU PROJET -------------------------------------------

ROOT_DIR = Path(__file__).resolve().parent.parent
# Résultat : ROOT_DIR pointe toujours sur la racine du projet,
# quel que soit l'endroit où le projet est installé sur l'ordinateur.

DATA_DIR   = ROOT_DIR / "data"
# - pointe vers le dossier qui contient les fichiers .sav

OUTPUT_DIR = ROOT_DIR / "output"
# - pointe vers le dossier où seront écrits tous les résultats

# -- FICHIERS SOURCES ---------------------------------------------

FILE_INDIV   = DATA_DIR / "indiv_SECTION_B.sav"
# Chemin complet vers la base individus (Section B)
# 1 712 428 lignes - le plus gros fichier du projet

FILE_HABITAT = DATA_DIR / "habitat_SECTION_E.sav"
# Chemin vers la base habitat/ménages (Section E)
# 188 550 lignes

FILE_DECES   = DATA_DIR / "deces_SECTION_C.sav"
# Chemin vers la base décès (Section C)

FILE_EMIGR   = DATA_DIR / "emigration_SECTION_D.sav"
# Chemin vers la base émigration (Section D)

FILE_AGRI    = DATA_DIR / "agriculture_F.sav"
# Chemin vers la base agriculture (Section F)

# -- IDENTIFIANTS CLÉS --------------------------------------------

# Clé ménage = combinaison district + numéro ménage
ID_DISTRICT = "A06"
# Nom de la colonne "numéro de district" dans les .sav
# A06 a 21 235 valeurs uniques - identifie chaque district

ID_MENAGE   = "A09"
# Nom de la colonne "numéro du ménage dans le district"
# A09 seul n'a que 78 valeurs (1 à 78) - insuffisant pour identifier un ménage

ID_KEY      = ["A06", "A09"]
# Clé composite : la VRAIE clé unique d'un ménage.
# Il faut les DEUX colonnes ensemble pour identifier un ménage sans ambiguïté.
# Découvert lors du diagnostic : A06 + A09 - 60 411 ménages uniques

ID_REGION   = "A01"   # Colonne région   (14 valeurs : 14 régions du Sénégal)
ID_DEPT     = "A02"   # Colonne département (46 valeurs)
ID_COMMUNE  = "A04"   # Colonne commune  (552 valeurs)
ID_MILIEU   = "A10"   # Colonne milieu   (1=Urbain, 2=Rural)
ID_INDIVIDU = "B01"   # N° d'ordre de l'individu dans son ménage

# -- PARAMÈTRES DE CONTRÔLE QUALITÉ (QAQC) -----------------------

AGE_MIN = 0
AGE_MAX = 120
# Bornes valides pour l'âge.
# Tout âge < 0 ou > 120 est considéré aberrant - remplacé par NaN.

# Seuil taille ménage : 99e percentile observé sur la base
# Au-delà de 125, les valeurs sont aberrantes (max observé légit. ~125)
TAILLE_MENAGE_MAX = 125
# Seuil fixé empiriquement à partir de la distribution réelle :
#   50e percentile  =  12 membres
#   75e percentile  =  46 membres
#   90e percentile  =  78 membres
#   99e percentile  = 125 membres  - seuil choisi
#   max observé     = 2182         - clairement aberrant
# Tout ménage avec plus de 125 membres - taille_menage = NaN

MISSING_CODES = [99, 999, 9999, 88, 888, 8888]
# Codes utilisés dans SPSS/la base pour signifier "valeur manquante" ou "NSP"
# (Ne Sait Pas). On les remplace tous par NaN (valeur manquante Python/pandas)
# pour que les calculs statistiques les ignorent automatiquement.
# Exemples : âge=99 signifie "inconnu", code=9999 signifie "non applicable"

CHUNK_SIZE = 100_000
# Nombre de lignes lues à la fois lors du chargement des gros fichiers .sav.
# indiv_SECTION_B.sav = 648 Mo, 1,7M lignes - impossible à charger d'un coup
# en mémoire (erreur "Unable to allocate 1.38 GiB").
# Solution : on lit 100 000 lignes, on traite, on lit les 100 000 suivantes, etc.
# Le tiret bas dans 100_000 est juste un séparateur visuel (= 100000).