"""
1_data_exploration/2_select_and_label/1_apply_hh_dict.py
=========================================================
Étape 2 - Sélection et étiquetage des variables ménage.

Sources  : habitat_SECTION_E.sav  +  indiv_SECTION_B.sav (CM uniquement)
Output   : output/labeled/hh_labeled.csv
"""
# Ce fichier fait deux choses :
# 1. SÉLECTION  : ne garder que les colonnes utiles (15 sur 388)
# 2. ÉTIQUETAGE : traduire les codes numériques en texte lisible


# -- IMPORTS ------------------------------------------------------

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
# Problème technique : ce fichier est dans un sous-dossier profond.
# Python ne saurait pas où trouver config.py et utils.py.
# .parents[2] remonte de 2 niveaux pour atteindre cleansurvey/
# sys.path.insert(0, ...) dit à Python : "cherche aussi dans ce dossier"
# - Permet d'écrire "from config import ..." sans erreur

import pandas as pd
import numpy as np
import pyreadstat

from config import (FILE_HABITAT, FILE_INDIV, OUTPUT_DIR,
                    MISSING_CODES, CHUNK_SIZE)
# On importe depuis config.py les chemins des fichiers et paramètres

from utils import save_csv, section_header
# On importe uniquement les fonctions dont on a besoin depuis utils.py


# ════════════════════════════════════════════════════════════════
# BLOC 1 - MAPPINGS DE RECODAGE
# Dictionnaires code numérique - label texte
# ════════════════════════════════════════════════════════════════

MILIEU_LBL = {1: "Urbain", 2: "Rural"}
# Dictionnaire Python : clé = code SPSS, valeur = label texte
# Quand on voit A10 = 1 dans la base - on écrit "Urbain"

TYPE_MENAGE_LBL = {1: "Ordinaire", 2: "Collectif"}
# A11 = 1 - "Ordinaire", A11 = 2 - "Collectif"

TYPE_MENAGE_COLLECTIF_LBL = {
    1: "Caserne", 2: "Couvent/Monastère", 3: "Hôtel/Auberge/Résidence",
    4: "Établissement pénitentiaire", 5: "Internat", 6: "Orphelinat",
    7: "Structure handicapés", 8: "Hôpitaux/Cliniques",
    9: "Daara moderne", 10: "Daara traditionnel",
    11: "Campus social universitaire", 12: "Chantier temporaire",
    13: "Campements/Abris provisoires", 14: "Campements touristiques",
    15: "Résidences corps diplomatique", 16: "Résidence étudiants",
}
# A11A = sous-type du ménage collectif (16 types possibles)
# Dans notre échantillon, A11A est à 100% NaN - aucun ménage collectif

SEXE_LBL = {1: "Masculin", 2: "Féminin"}
# B06 = 1 - "Masculin", B06 = 2 - "Féminin"

NIVEAU_ETUDE_LBL = {
    0: "Aucun", 1: "CFEE/CEPE", 2: "DFEM/BFEM", 3: "CAP",
    4: "BEP/BEPC", 5: "BP", 6: "BT", 7: "BAC", 8: "DTS",
    9: "DUT", 10: "BTS", 11: "DUEL/DEUG", 12: "Licence",
    13: "Maîtrise", 14: "Master", 15: "DEA/DESS",
    16: "Diplôme ingénieur", 17: "Doctorat",
}
# B33 = diplôme le plus élevé du CM
# 18 niveaux possibles, du plus bas (0=Aucun) au plus haut (17=Doctorat)

SITUATION_MATRIMONIALE_LBL = {
    0: "Monogame", 1: "Polygame – 1ère épouse",
    2: "Polygame – 2ème épouse", 3: "Polygame – 3ème épouse",
    4: "Polygame – 4ème épouse", 5: "Polygame – 5ème épouse ou +",
    6: "Célibataire", 7: "Veuf/Veuve",
    8: "Divorcé(e)", 9: "Union libre", 10: "Séparé(e)",
}
# B41 = situation matrimoniale du CM
# Note : 0 = Monogame (marié avec une seule épouse)
# 1 à 5 = Polygame (la position de l'épouse dans le mariage)

STATUT_EMPLOI_LBL = {
    1: "Occupé", 2: "Chômeur ayant déjà travaillé",
    3: "À la recherche d'un premier emploi", 4: "Occupé au foyer",
    5: "Étudiant/Élève", 6: "Rentier",
    7: "Pensionné (FNR ou IPRES)",
    8: "Personne du 3e âge non pensionnée", 9: "Autres inactifs",
}
# B36 = situation par rapport à l'emploi au cours des 12 derniers mois
# "Occupé" = travaille. FNR = Fonds National de Retraite, IPRES = caisse retraite privée

SECTEUR_INSTIT_LBL = {
    1: "Public", 2: "Privé formel",
    3: "Informel", 4: "ISBLSM (ONG, ASC, Fondations…)",
}
# B39B = secteur institutionnel de l'employeur du CM
# ISBLSM = Institutions Sans But Lucratif au Service des Ménages


# ════════════════════════════════════════════════════════════════
# BLOC 2 - LISTES DE COLONNES À SÉLECTIONNER
# ════════════════════════════════════════════════════════════════

COLS_B = ["A06", "A09", "B04", "AGE_CM", "B06", "B33", "B41", "B36", "B39A", "B39B"]
# Les 10 colonnes qu'on garde de la Section B (sur 146 disponibles).
# A06, A09  - clé ménage (district + numéro)
# B04       - lien de parenté (pour filtrer le CM : B04 == 1)
# AGE_CM    - âge du CM (colonne précalculée dans la base)
# B06       - sexe du CM
# B33       - niveau d'études du CM
# B41       - situation matrimoniale du CM
# B36       - statut d'emploi du CM
# B39A      - branche d'activité ISIC Rev 4 (code à 4 chiffres)
# B39B      - secteur institutionnel

COLS_E = ["A06", "A09", "A01", "A02", "A04", "A10", "A11", "A11A"]
# Les 8 colonnes qu'on garde de la Section E (sur 242 disponibles).
# A06, A09  - clé ménage
# A01       - région
# A02       - département
# A04       - commune
# A10       - milieu (urbain/rural)
# A11       - type de ménage (ordinaire/collectif)
# A11A      - sous-type si collectif


# ════════════════════════════════════════════════════════════════
# FONCTION 1 - lire_colonnes_sav()
# Lire uniquement les colonnes utiles d'un .sav
# ════════════════════════════════════════════════════════════════

def lire_colonnes_sav(filepath: str, colonnes: list, chunksize: int = CHUNK_SIZE) -> pd.DataFrame:
    """
    Lit un fichier .sav en ne chargeant que les colonnes demandées.
    """
    path = Path(filepath)
    size_mb = path.stat().st_size / (1024 * 1024)
    print(f"  ⏳ {path.name} ({size_mb:.0f} Mo) - colonnes sélectionnées : {colonnes}")

    chunks = []
    total  = 0
    for df_chunk, meta in pyreadstat.read_file_in_chunks(
        pyreadstat.read_sav, str(path),
        chunksize=chunksize,
        apply_value_formats=False,
        formats_as_category=False
    ):
        df_chunk.columns = [c.upper() for c in df_chunk.columns]

        cols_dispo = [c for c in colonnes if c in df_chunk.columns]
        # On vérifie que chaque colonne demandée existe bien dans le chunk.
        # Si une colonne est absente (ex : AGE_CM absent dans certains fichiers),
        # on ne plante pas - on prend juste ce qui est disponible.

        chunks.append(df_chunk[cols_dispo])
        # On ne garde QUE ces colonnes - le chunk passe de 146 à 10 colonnes.
        # Résultat : beaucoup moins de mémoire utilisée.
        # C'est ce qui résout l'erreur "Unable to allocate 1.38 GiB".

        total += len(df_chunk)
        print(f"     ... {total:,} lignes lues", end="\r")

    df = pd.concat(chunks, ignore_index=True)
    print(f"  ✔ {path.name} - {df.shape[0]:,} lignes, {df.shape[1]} colonnes          ")
    return df


def recode_missing_cols(df: pd.DataFrame, missing_codes: list) -> pd.DataFrame:
    """Remplace les codes manquants sur un petit DataFrame (colonnes déjà filtrées)."""
    return df.replace(missing_codes, np.nan)
    # Identique à recode_missing() dans utils.py mais on l'appelle ici
    # APRÈS avoir filtré les colonnes - le DataFrame est petit (10 colonnes)
    # plus d'erreur mémoire


# ════════════════════════════════════════════════════════════════
# FONCTION 2 - extraire_cm()
# Isoler les chefs de ménage depuis la Section B
# ════════════════════════════════════════════════════════════════

def extraire_cm(df_indiv: pd.DataFrame) -> pd.DataFrame:
    """Filtre les CM (B04 == 1) et sélectionne les variables utiles."""

    df_cm = df_indiv[df_indiv["B04"] == 1].copy()
    # df_indiv["B04"] == 1 - masque booléen : True pour les chefs de ménage
    # B04 = lien de parenté avec le CM
    # B04 == 1 signifie "c'est le chef de ménage lui-même"
    # On filtre : on ne garde que les lignes où B04 == 1
    # .copy() - copie indépendante pour éviter les bugs de modification

    df_cm = df_cm.rename(columns={
        "AGE_CM": "age_cm",
        "B06": "sexe_cm",
        "B33": "niveau_etude_cm",
        "B41": "situation_matrimoniale_cm",
        "B36": "statut_emploi_cm",
        "B39A": "branche_isic_cm",
        "B39B": "secteur_instit_cm",
    })
    # On renomme les colonnes avec des noms explicites.
    # "B06" ne dit rien - "sexe_cm" est immédiatement compréhensible.
    # C'est la partie ÉTIQUETAGE des noms de colonnes.

    df_cm = df_cm.drop_duplicates(subset=["A06", "A09"], keep="first")
    # Sécurité : si un ménage a plusieurs lignes avec B04==1 (doublon),
    # on ne garde que la première occurrence.
    # keep="first" - garde la première ligne rencontrée en cas de doublon.

    print(f"  - {len(df_cm):,} chefs de ménage extraits")
    return df_cm


# ════════════════════════════════════════════════════════════════
# FONCTION 3 - extraire_habitat()
# Préparer les variables de la Section E
# ════════════════════════════════════════════════════════════════

def extraire_habitat(df_habitat: pd.DataFrame) -> pd.DataFrame:
    """Renomme et déduplique les variables habitat."""

    df_h = df_habitat.rename(columns={
        "A01": "region",
        "A02": "departement",
        "A04": "commune",
        "A10": "milieu",
        "A11": "type_menage",
        "A11A": "type_menage_collectif",
    })
    # Même logique : on remplace les codes questionnaire (A01, A10...)
    # par des noms compréhensibles (region, milieu...)

    df_h = df_h.drop_duplicates(subset=["A06", "A09"], keep="first")
    # La Section E peut avoir plusieurs lignes par ménage.
    # On garde une seule ligne par ménage (identifié par A06+A09).

    print(f"  - {len(df_h):,} ménages dans Section E")
    return df_h


# ════════════════════════════════════════════════════════════════
# FONCTION 4 - calculer_taille_menage()
# Compter le nombre de membres par ménage
# ════════════════════════════════════════════════════════════════

def calculer_taille_menage(df_indiv: pd.DataFrame) -> pd.DataFrame:
    """Calcule la taille du ménage par A06+A09."""

    taille = (
        df_indiv.groupby(["A06", "A09"])
        # groupby : regroupe toutes les lignes qui ont le même A06 ET A09
        # = toutes les personnes du même ménage sont regroupées ensemble

        .size()
        # .size() compte le nombre de lignes dans chaque groupe
        # = nombre de membres dans chaque ménage

        .reset_index(name="taille_menage")
        # Transforme le résultat en DataFrame avec 3 colonnes :
        # A06 | A09 | taille_menage
        # reset_index remet A06 et A09 comme colonnes normales
    )

    print(f"  - {len(taille):,} ménages distincts (A06+A09)")
    print(f"  - Taille moyenne : {taille['taille_menage'].mean():.2f}")
    return taille


# ════════════════════════════════════════════════════════════════
# FONCTION 5 - appliquer_labels()
# Traduire tous les codes en texte lisible
# ════════════════════════════════════════════════════════════════

def appliquer_labels(df: pd.DataFrame) -> pd.DataFrame:
    """Recode les codes numériques en labels texte."""

    mappings = {
        "milieu":                    MILIEU_LBL,
        "type_menage":               TYPE_MENAGE_LBL,
        "type_menage_collectif":     TYPE_MENAGE_COLLECTIF_LBL,
        "sexe_cm":                   SEXE_LBL,
        "niveau_etude_cm":           NIVEAU_ETUDE_LBL,
        "situation_matrimoniale_cm": SITUATION_MATRIMONIALE_LBL,
        "statut_emploi_cm":          STATUT_EMPLOI_LBL,
        "secteur_instit_cm":         SECTEUR_INSTIT_LBL,
    }
    # Dictionnaire des correspondances : nom de colonne - mapping à appliquer
    # Ex : la colonne "milieu" doit être recodée avec MILIEU_LBL

    df = df.copy()
    for col, mp in mappings.items():
        # On parcourt chaque paire (nom_colonne, mapping)
        if col in df.columns:
            # Sécurité : on applique le mapping seulement si la colonne existe
            df[col] = df[col].map(mp)
            # .map(dictionnaire) : pour chaque valeur de la colonne,
            # cherche la clé dans le dictionnaire et retourne la valeur.
            # Ex : df["milieu"] = [1, 2, 1, 1] - ["Urbain", "Rural", "Urbain", "Urbain"]
            # Si la clé n'existe pas dans le dictionnaire - NaN automatiquement
    return df


# ════════════════════════════════════════════════════════════════
# FONCTION PRINCIPALE - main()
# Orchestre toutes les étapes dans l'ordre
# ════════════════════════════════════════════════════════════════

def main():
    section_header("ÉTAPE 2 - SÉLECTION & ÉTIQUETAGE VARIABLES MÉNAGE")

    # ÉTAPE A : Chargement ciblé Section E (8 colonnes seulement)
    print("\n[Habitat - Section E]")
    df_habitat = lire_colonnes_sav(str(FILE_HABITAT), COLS_E)
    df_habitat = recode_missing_cols(df_habitat, MISSING_CODES)
    # On lit le fichier puis on remplace immédiatement les codes manquants.
    # Fichier petit (8 colonnes) - pas de problème mémoire.

    # ÉTAPE B : Chargement ciblé Section B (10 colonnes seulement)
    print("\n[Individus - Section B  (colonnes CM uniquement)]")
    df_indiv = lire_colonnes_sav(str(FILE_INDIV), COLS_B)
    df_indiv = recode_missing_cols(df_indiv, MISSING_CODES)
    # Même logique. Réduit de 146 - 10 colonnes - résout l'erreur mémoire.

    # ÉTAPE C : Calcul de la taille de chaque ménage
    print("\n[Calcul taille ménage]")
    df_taille = calculer_taille_menage(df_indiv)
    # On compte combien de personnes sont dans chaque ménage (A06+A09).
    # Résultat : un DataFrame avec une ligne par ménage + colonne taille_menage.

    # ÉTAPE D : Extraction des chefs de ménage
    print("\n[Extraction Chef de Ménage]")
    df_cm = extraire_cm(df_indiv)
    # On filtre B04==1 pour ne garder qu'une ligne par ménage (le CM).
    # Résultat : ~60 783 chefs de ménage avec leurs caractéristiques.

    # ÉTAPE E : Préparation des variables habitat
    print("\n[Sélection variables habitat]")
    df_h = extraire_habitat(df_habitat)
    # On renomme les colonnes et déduplique.
    # Résultat : ~60 771 ménages avec région, commune, milieu, type.

    # ÉTAPE F : Fusion des trois tables
    print("\n[Fusion]")
    df_menage = df_h.merge(df_taille, on=["A06", "A09"], how="left")
    # merge = jointure SQL entre df_h et df_taille sur la clé A06+A09.
    # how="left" - on garde TOUS les ménages de df_h (table de gauche),
    # même si certains n'ont pas de taille calculée (NaN alors).
    # Résultat : habitat + taille_menage

    df_menage = df_menage.merge(df_cm, on=["A06", "A09"], how="left")
    # Deuxième fusion : on ajoute les caractéristiques du CM.
    # how="left" - on garde tous les ménages même sans CM identifié.
    # Résultat final : habitat + taille + caractéristiques CM = 17 colonnes

    print(f"  - Table ménage : {len(df_menage):,} lignes × {df_menage.shape[1]} colonnes")

    # ÉTAPE G : Application des labels
    df_menage = appliquer_labels(df_menage)
    # On traduit tous les codes numériques en texte.
    # Ex : sexe_cm passe de [1, 2, 1] à ["Masculin", "Féminin", "Masculin"]

    # ÉTAPE H : Export
    save_csv(df_menage, OUTPUT_DIR / "labeled" / "hh_labeled.csv", label="hh_labeled.csv")
    # On sauvegarde la table dans output/labeled/hh_labeled.csv
    # C'est l'input de l'étape suivante (nettoyage).


if __name__ == "__main__":
    main()
# "__name__ == '__main__'" signifie :
# "exécute main() seulement si ce fichier est lancé directement"
# (pas quand il est importé par un autre script comme run_all.py)