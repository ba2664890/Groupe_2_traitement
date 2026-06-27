"""
utils.py - Fonctions utilitaires partagées (Groupe 2)
Lecture .sav avec gestion mémoire, exports, logs.
"""
# Ce fichier contient des fonctions réutilisables par TOUS les scripts
# du pipeline. On écrit une fonction une seule fois ici, et tous les
# autres fichiers l'importent.


# -- IMPORTS ------------------------------------------------------

import pyreadstat
# Bibliothèque spécialisée pour lire les fichiers SPSS (.sav).
# C'est l'équivalent de "haven" en R.

import pandas as pd
# La bibliothèque centrale de manipulation de données en Python.
# Elle fournit le DataFrame - notre tableau de données principal.

from pathlib import Path
# Pour manipuler les chemins de fichiers (déjà vu dans config.py).

from config import CHUNK_SIZE, MISSING_CODES
# On importe les constantes depuis config.py.
# Ainsi si on change CHUNK_SIZE dans config.py, utils.py s'adapte
# automatiquement sans qu'on touche à ce fichier.

import numpy as np
# NumPy est la bibliothèque de calcul numérique.
# On l'utilise ici uniquement pour np.nan - la valeur "manquant"


# ════════════════════════════════════════════════════════════════
# FONCTION 1 - read_sav()
# Lire un fichier .sav en gérant la mémoire
# ════════════════════════════════════════════════════════════════

def read_sav(filepath: str | Path, chunksize: int = CHUNK_SIZE) -> pd.DataFrame:
    # Définition de la fonction :
    # - filepath     : chemin du fichier .sav à lire (str ou Path)
    # - chunksize    : nb de lignes par chunk (défaut = 100 000 depuis config)
    # - -> pd.DataFrame : la fonction retourne un DataFrame pandas
    """
    Lit un fichier .sav (SPSS).
    - Fichiers < 50 Mo : lecture directe.
    - Fichiers >= 50 Mo : lecture par chunks pour éviter les erreurs mémoire.
    Retourne un DataFrame avec des colonnes en MAJUSCULES.
    """

    path = Path(filepath)
    # Convertit le chemin en objet Path (au cas où c'est une simple chaîne)

    if not path.exists():
        raise FileNotFoundError(f"Fichier introuvable : {path}")
    # Vérifie que le fichier existe avant d'essayer de le lire.
    # Si non - arrête le programme avec un message clair.
    # Vaut mieux un message d'erreur explicite qu'un plantage cryptique.

    size_mb = path.stat().st_size / (1024 * 1024)
    # path.stat().st_size - taille du fichier en octets
    # / (1024 * 1024)     - conversion en mégaoctets

    if size_mb < 50:
        # -- CAS 1 : fichier léger (< 50 Mo) - lecture directe --
        df, _ = pyreadstat.read_sav(
            str(path),
            apply_value_formats=False,
            # False = on garde les CODES numériques (1, 2...)
            # pas les labels texte ("Masculin", "Féminin"...)
            # On appliquera les labels nous-mêmes dans 1_apply_hh_dict.py
            formats_as_category=False
            # False = on ne convertit pas en type "catégorie" pandas
            # Plus simple à manipuler en gardant les types numériques bruts
        )
        # pyreadstat.read_sav retourne 2 objets : le DataFrame ET les métadonnées

        df.columns = [c.upper() for c in df.columns]
        # Met tous les noms de colonnes en MAJUSCULES.
        # Raison : SPSS peut exporter "a01" ou "A01" selon les versions.
        # En forçant les majuscules, on évite les bugs du type
        # "colonne 'a06' introuvable" alors qu'elle s'appelle 'A06'.

        print(f"  {path.name} - {len(df):,} lignes, {df.shape[1]} colonnes")
        return df
        # Retourne le DataFrame complet

    # -- CAS 2 : gros fichier (>= 50 Mo) - lecture par chunks --
    print(f"  ⏳ {path.name} ({size_mb:.0f} Mo) - lecture par chunks de {chunksize:,}...")

    chunks = []
    # Liste vide qui va accumuler les morceaux (chunks) lus

    total = 0
    # Compteur pour afficher la progression

    for df_chunk, _ in pyreadstat.read_file_in_chunks(
        pyreadstat.read_sav, str(path),
        chunksize=chunksize,        # 100 000 lignes à la fois
        apply_value_formats=False,
        formats_as_category=False
    ):
    # read_file_in_chunks lit le fichier morceau par morceau.
    # À chaque tour de boucle, df_chunk contient 100 000 lignes.
    # La boucle tourne jusqu'à ce que tout le fichier soit lu.

        df_chunk.columns = [c.upper() for c in df_chunk.columns]
        # Même normalisation en majuscules sur chaque chunk

        chunks.append(df_chunk)
        # On ajoute le chunk à la liste

        total += len(df_chunk)
        # On cumule le nombre de lignes lues

        print(f"     ... {total:,} lignes lues", end="\r")
        # end="\r" : efface la ligne précédente dans le terminal
        # et réécrit par-dessus - effet de compteur qui défile

    df = pd.concat(chunks, ignore_index=True)
    # pd.concat : colle tous les chunks verticalement en un seul DataFrame
    # ignore_index=True : recrée un index propre de 0 à N
    # (sinon chaque chunk aurait son propre index 0-99999)

    print(f" {path.name} - {df.shape[0]:,} lignes, {df.shape[1]} colonnes          ")
    # Les espaces à la fin effacent le compteur de progression affiché avant
    return df


# ════════════════════════════════════════════════════════════════
# FONCTION 2 - recode_missing()
# Remplacer les codes manquants par NaN
# ════════════════════════════════════════════════════════════════

def recode_missing(df: pd.DataFrame,
                   missing_codes: list = MISSING_CODES) -> pd.DataFrame:
    """Remplace les codes manquants conventionnels par NaN."""

    return df.replace(missing_codes, np.nan)
    # df.replace(liste, valeur) : cherche chaque valeur de la liste
    # dans tout le DataFrame et la remplace par np.nan.
    # Ex : partout où il y a 99, 999, 9999, 88, 888 ou 8888 - NaN
    # NaN est reconnu par pandas comme "manquant" - ignoré dans les calculs.
    # ATTENTION : cette fonction charge tout le DataFrame en mémoire.
    # C'est pourquoi dans 1_apply_hh_dict.py on l'appelle APRÈS
    # avoir sélectionné uniquement les colonnes utiles.


# ════════════════════════════════════════════════════════════════
# FONCTION 3 - flag_aberrants()
# Détecter et corriger les valeurs hors bornes
# ════════════════════════════════════════════════════════════════

def flag_aberrants(df: pd.DataFrame, col: str,
                   vmin: float = None, vmax: float = None,
                   label: str = "") -> pd.DataFrame:
    """
    Remplace par NaN les valeurs hors bornes sur une colonne numérique.
    """

    if col not in df.columns:
        return df
    # Sécurité : si la colonne n'existe pas, on retourne le df inchangé.
    # Évite un plantage si une colonne est absente dans un fichier.

    mask = pd.Series(False, index=df.index)
    # On crée un masque booléen : une série de True/False de la même
    # taille que le DataFrame. Au départ tout est False (= "pas aberrant").

    if vmin is not None:
        mask |= df[col] < vmin
    # |= signifie "OU égal" : si la valeur est < vmin, le masque passe à True
    # pour cette ligne. Ex : âge < 0 - True

    if vmax is not None:
        mask |= df[col] > vmax
    # De même pour le maximum. Ex : âge > 120 - True
    # Une ligne est aberrante si elle dépasse le min OU le max.

    n = mask.sum()
    # .sum() sur un masque booléen compte le nombre de True
    # - nombre de valeurs aberrantes trouvées

    if n > 0:
        print(f"  {n} valeur(s) aberrante(s) sur {col} {label} - NaN")
        df = df.copy()
        # .copy() crée une copie du DataFrame avant de le modifier.
        # En pandas, modifier directement peut affecter l'original
        # (problème de "vue" vs "copie"). Le .copy() évite ce bug.

        df.loc[mask, col] = np.nan
        # df.loc[masque, colonne] : sélectionne uniquement les lignes
        # où le masque est True, dans la colonne spécifiée,
        # et remplace par NaN.

    return df


# ════════════════════════════════════════════════════════════════
# FONCTION 4 - save_csv()
# Sauvegarder un DataFrame en fichier CSV
# ════════════════════════════════════════════════════════════════

def save_csv(df: pd.DataFrame, path: str | Path, label: str = "") -> None:
    # -> None : cette fonction ne retourne rien, elle écrit un fichier.
    """Sauvegarde un DataFrame en CSV UTF-8 avec BOM (compatible Excel)."""

    path = Path(path)

    path.parent.mkdir(parents=True, exist_ok=True)
    # Crée le dossier de destination s'il n'existe pas encore.
    # parents=True  : crée aussi les dossiers parents si nécessaire
    # exist_ok=True : ne plante pas si le dossier existe déjà

    df.to_csv(path, index=False, encoding="utf-8-sig")
    # index=False    : n'écrit pas la colonne d'index pandas (0, 1, 2...)
    #                  dans le fichier - on ne veut que nos vraies colonnes
    # encoding="utf-8-sig" : UTF-8 avec BOM (Byte Order Mark)
    #                  Le BOM est un marqueur invisible en début de fichier
    #                  qui indique à Excel que c'est de l'UTF-8.
    #                  Sans lui, Excel affiche mal les accents (é, è, à...).

    print(f" {label or path.name} - {path}  ({len(df):,} lignes)")
    # label or path.name : affiche le label si fourni, sinon le nom du fichier


# ════════════════════════════════════════════════════════════════
# FONCTION 5 - section_header()
# Afficher un titre de section dans la console
# ════════════════════════════════════════════════════════════════

def section_header(titre: str) -> None:
    """Affiche un séparateur de section dans la console."""
    print(f"\n{'=' * 55}")
    # '=' * 55 - répète le caractère '=' 55 fois
    # Produit : =======================================================
    print(f"  {titre}")
    print(f"{'=' * 55}")