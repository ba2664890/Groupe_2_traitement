"""
2_clean_and_merge/1_clean_hh_ind.py
====================================
Étape 3 - Nettoyage de la table ménage.

Source  : output/labeled/hh_labeled.csv
Output  : output/clean/hh_clean.csv
          output/clean/hh_qaqc_log.csv
"""
# Ce fichier reçoit hh_labeled.csv (table avec labels texte)
# et applique tous les contrôles qualité (QAQC) :
#   - Suppression des colonnes inutiles
#   - Valeurs aberrantes (âge, taille ménage)
#   - Codes invalides (sexe, milieu, statut emploi...)
#   - Incohérences logiques (sexe vs situation matrimoniale, âge vs statut)
# Tout ce qui est corrigé ou signalé est enregistré dans hh_qaqc_log.csv


# -- IMPORTS ------------------------------------------------------

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
# Ce fichier est dans 2_clean_and_merge/ - .parents[1] remonte
# d'un niveau vers cleansurvey/ pour trouver config.py et utils.py

import pandas as pd
import numpy as np

from config import OUTPUT_DIR, AGE_MIN, AGE_MAX, TAILLE_MENAGE_MAX
# On importe uniquement les constantes dont on a besoin :
# - OUTPUT_DIR       : dossier de sortie
# - AGE_MIN / AGE_MAX : bornes [0, 120] pour détecter les âges aberrants
# - TAILLE_MENAGE_MAX : seuil 125 (99e percentile)

from utils import save_csv, section_header


# ════════════════════════════════════════════════════════════════
# BLOC 1 - ENSEMBLES DE VALEURS VALIDES
# Servent à vérifier que les codes dans la base sont légitimes
# ════════════════════════════════════════════════════════════════

SEXE_VALIDES = {"Masculin", "Féminin"}
# Un ensemble (set) Python : structure optimisée pour vérifier
# si une valeur appartient à une liste. Plus rapide qu'une liste.
# Toute valeur de sexe_cm qui n'est pas dans cet ensemble - invalide

STATUT_EMPLOI_VALIDES = {
    "Occupé", "Chômeur ayant déjà travaillé",
    "À la recherche d'un premier emploi", "Occupé au foyer",
    "Étudiant/Élève", "Rentier", "Pensionné (FNR ou IPRES)",
    "Personne du 3e âge non pensionnée", "Autres inactifs",
}
# Les 9 modalités valides de statut_emploi_cm (issues du questionnaire B36)
# Toute autre valeur après étiquetage = code non reconnu = NaN

SITUATION_MATRI_VALIDES = {
    "Monogame", "Polygame – 1ère épouse", "Polygame – 2ème épouse",
    "Polygame – 3ème épouse", "Polygame – 4ème épouse",
    "Polygame – 5ème épouse ou +", "Célibataire",
    "Veuf/Veuve", "Divorcé(e)", "Union libre", "Séparé(e)",
}
# Les 11 modalités valides de situation_matrimoniale_cm (B41)

MILIEU_VALIDES = {"Urbain", "Rural"}
# Seulement 2 valeurs possibles pour le milieu


# ════════════════════════════════════════════════════════════════
# FONCTION 1 - supprimer_colonnes_parasites()
# Nettoyer les colonnes inutiles dans la table
# ════════════════════════════════════════════════════════════════

def supprimer_colonnes_parasites(df: pd.DataFrame, log: list) -> pd.DataFrame:
    """Supprime les colonnes techniques et celles entièrement vides."""

    a_supprimer = [c for c in ["B04", "type_menage_collectif"] if c in df.columns]
    # Liste en compréhension : on cherche B04 et type_menage_collectif
    # dans les colonnes du DataFrame. On ne liste que celles qui existent.
    # B04 = variable filtre (lien de parenté) - sert à identifier le CM
    #       mais n'a pas sa place dans la table finale
    # type_menage_collectif = 100% NaN dans notre échantillon - inutile

    if "type_menage_collectif" in df.columns:
        if df["type_menage_collectif"].notna().sum() > 0:
            a_supprimer.remove("type_menage_collectif")
    # Sécurité : on ne supprime type_menage_collectif QUE si elle est
    # vraiment 100% vide. .notna().sum() compte les valeurs non-NaN.
    # Si > 0, il y a des données - on la garde.
    # Cette vérification rend le code robuste pour un futur recensement
    # où des ménages collectifs pourraient être présents.

    if a_supprimer:
        df = df.drop(columns=a_supprimer)
        # .drop(columns=liste) supprime les colonnes spécifiées

        log.append({
            "controle": "Colonnes supprimées",
            "nb_cas": len(a_supprimer),
            "action": f"Supprimé : {a_supprimer}"
        })
        # On enregistre l'action dans le log QAQC.
        # log est une liste de dictionnaires. Chaque dictionnaire = 1 contrôle.
        # À la fin, log sera converti en DataFrame et sauvegardé en CSV.

        print(f"  Colonnes supprimées : {a_supprimer}")
    return df


# ════════════════════════════════════════════════════════════════
# FONCTION 2 - nettoyer_age_cm()
# Détecter et corriger les âges aberrants du CM
# ════════════════════════════════════════════════════════════════

def nettoyer_age_cm(df: pd.DataFrame, log: list) -> pd.DataFrame:
    """Remplace les âges CM hors bornes par NaN."""

    if "age_cm" not in df.columns:
        return df
    # Sécurité : si la colonne n'existe pas, on sort sans modifier

    mask = df["age_cm"].notna() & (
        (df["age_cm"] < AGE_MIN) | (df["age_cm"] > AGE_MAX)
    )
    # Masque en deux conditions combinées avec & (ET) et | (OU) :
    # .notna()        - on ignore les NaN déjà présents (pas la peine de les re-traiter)
    # < AGE_MIN (0)   - âge négatif = aberrant
    # > AGE_MAX (120) - âge > 120 ans = aberrant
    # Une ligne est aberrante si elle n'est pas NaN ET (trop petite OU trop grande)

    n = mask.sum()
    # Compte le nombre de True dans le masque = nb de valeurs aberrantes

    if n > 0:
        log.append({"controle": "age_cm hors bornes", "nb_cas": n,
                    "action": f"NaN (bornes : {AGE_MIN}–{AGE_MAX})"})
        print(f"   age_cm : {n} valeur(s) hors [{AGE_MIN}, {AGE_MAX}] - NaN")
        df = df.copy()
        df.loc[mask, "age_cm"] = np.nan
        # df.loc[masque, colonne] = np.nan
        # Sélectionne uniquement les lignes aberrantes et remplace par NaN
    return df


# ════════════════════════════════════════════════════════════════
# FONCTION 3 - nettoyer_taille_menage()
# Détecter les tailles de ménage aberrantes
# ════════════════════════════════════════════════════════════════

def nettoyer_taille_menage(df: pd.DataFrame, log: list) -> pd.DataFrame:
    """
    Seuil basé sur le 99e percentile observé (125 membres).
    Au-delà : valeur aberrante - NaN.
    """

    if "taille_menage" not in df.columns:
        return df

    mask = df["taille_menage"].notna() & (df["taille_menage"] > TAILLE_MENAGE_MAX)
    # On cherche les ménages avec plus de 125 membres.
    # Ce seuil a été fixé empiriquement :
    #   99% des ménages ont ≤ 125 membres - tout ce qui dépasse est aberrant.
    # Dans nos données : max observé = 2182 - clairement une erreur de saisie.

    n = mask.sum()
    if n > 0:
        log.append({
            "controle": "taille_menage aberrante",
            "nb_cas": n,
            "action": f"NaN (seuil = 99e percentile = {TAILLE_MENAGE_MAX})"
        })
        print(f"   taille_menage : {n} ménage(s) > {TAILLE_MENAGE_MAX} - NaN")
        df = df.copy()
        df.loc[mask, "taille_menage"] = np.nan
    return df


# ════════════════════════════════════════════════════════════════
# FONCTION 4 - verifier_codes()
# Vérifier que les modalités texte sont dans la liste valide
# ════════════════════════════════════════════════════════════════

def verifier_codes(df: pd.DataFrame, col: str, valides: set, log: list) -> pd.DataFrame:
    """Remplace les modalités inconnues par NaN."""

    if col not in df.columns:
        return df

    mask = df[col].notna() & ~df[col].isin(valides)
    # ~df[col].isin(valides) - le ~ signifie "NON"
    # .isin(valides) = True si la valeur est dans l'ensemble valide
    # ~ inverse : True si la valeur N'EST PAS dans l'ensemble
    # Combiné avec .notna() : on cherche les valeurs non-NaN et invalides

    n = mask.sum()
    if n > 0:
        log.append({"controle": f"code invalide - {col}", "nb_cas": n,
                    "action": "NaN"})
        print(f"   {col} : {n} code(s) invalide(s) - NaN")
        df = df.copy()
        df.loc[mask, col] = np.nan
    return df
    # Cette fonction est générique : on l'appelle 4 fois dans main()
    # avec des colonnes et des ensembles de valides différents.
    # C'est du code réutilisable = bonne pratique.


# ════════════════════════════════════════════════════════════════
# FONCTION 5 - coherence_sexe_polygamie()
# Contrôle logique : sexe vs situation matrimoniale
# ════════════════════════════════════════════════════════════════

def coherence_sexe_polygamie(df: pd.DataFrame, log: list) -> pd.DataFrame:
    """CM masculin déclaré épouse en polygamie - incohérence."""

    if "sexe_cm" not in df.columns or "situation_matrimoniale_cm" not in df.columns:
        return df

    epouses = {"Polygame – 1ère épouse", "Polygame – 2ème épouse",
               "Polygame – 3ème épouse", "Polygame – 4ème épouse",
               "Polygame – 5ème épouse ou +"}
    # Ensemble des modalités qui correspondent à une position d'épouse

    mask = (df["sexe_cm"] == "Masculin") & df["situation_matrimoniale_cm"].isin(epouses)
    # Incohérence : un homme ne peut pas être "épouse" dans une polygamie
    # Les deux conditions doivent être vraies en même temps (&)
    # - c'est une erreur de saisie dans la base

    n = mask.sum()
    if n > 0:
        log.append({"controle": "CM masculin déclaré épouse", "nb_cas": n,
                    "action": "situation_matrimoniale_cm - NaN"})
        print(f"  {n} CM masculin(s) déclaré(s) épouse - NaN")
        df = df.copy()
        df.loc[mask, "situation_matrimoniale_cm"] = np.nan
        # On corrige la situation matrimoniale - NaN (pas le sexe)
        # car le sexe est plus fiable que la situation matrimoniale
    return df


# ════════════════════════════════════════════════════════════════
# FONCTION 6 - coherence_age_statut()
# Contrôle logique : âge vs statut d'emploi
# ════════════════════════════════════════════════════════════════

def coherence_age_statut(df: pd.DataFrame, log: list) -> pd.DataFrame:
    """CM 'Étudiant/Élève' avec âge >= 60 ans - signalement."""

    if "age_cm" not in df.columns or "statut_emploi_cm" not in df.columns:
        return df

    mask = (df["statut_emploi_cm"] == "Étudiant/Élève") & (df["age_cm"] >= 60)
    # Un chef de ménage étudiant à 60 ans ou plus est très improbable.
    # Ce n'est pas impossible (formation continue, daara...) donc on
    # SIGNALE sans corriger automatiquement - action = "Signalement"

    n = mask.sum()
    if n > 0:
        log.append({"controle": "CM Étudiant >= 60 ans", "nb_cas": n,
                    "action": "Signalement"})
        print(f"   {n} CM 'Étudiant/Élève' avec âge >= 60 ans (à vérifier)")
    return df
    # Différence importante avec les fonctions précédentes :
    # ici on ne modifie PAS la valeur - on laisse le statisticien (analyste) décider


# ════════════════════════════════════════════════════════════════
# FONCTION 7 - coherence_age_retraite()
# Contrôle logique : âge vs pension
# ════════════════════════════════════════════════════════════════

def coherence_age_retraite(df: pd.DataFrame, log: list) -> pd.DataFrame:
    """CM 'Pensionné' avec âge < 45 ans - signalement."""

    if "age_cm" not in df.columns or "statut_emploi_cm" not in df.columns:
        return df

    mask = (df["statut_emploi_cm"] == "Pensionné (FNR ou IPRES)") & (df["age_cm"] < 45)
    # Un retraité de moins de 45 ans est suspect.
    # L'âge légal de retraite au Sénégal est 60-65 ans.
    # Seuil à 45 pour être conservateur (retraite militaire anticipée possible).
    # - Signalement sans correction automatique

    n = mask.sum()
    if n > 0:
        log.append({"controle": "CM pensionné < 45 ans", "nb_cas": n,
                    "action": "Signalement"})
        print(f"   {n} CM pensionné(s) avec âge < 45 ans (à vérifier)")
    return df


# ════════════════════════════════════════════════════════════════
# FONCTION 8 - stats_nettoyage()
# Afficher un résumé des statistiques clés après nettoyage
# ════════════════════════════════════════════════════════════════

def stats_nettoyage(df: pd.DataFrame) -> None:
    """Affiche un résumé statistique après nettoyage."""

    print("\n  Résumé après nettoyage :")
    print(f"    Nb ménages total           : {len(df):,}")

    if "taille_menage" in df.columns:
        print(f"    Taille moy. ménage         : {df['taille_menage'].mean():.2f}")
        print(f"    Taille médiane ménage      : {df['taille_menage'].median():.0f}")
        print(f"    Taille max ménage          : {int(df['taille_menage'].max())}")
        # .mean()   = moyenne arithmétique
        # .median() = valeur du milieu (50e percentile) - moins sensible aux extrêmes
        # .max()    = valeur maximale après nettoyage

    if "milieu" in df.columns:
        for k, v in df["milieu"].value_counts(normalize=True).mul(100).round(1).items():
            print(f"    Milieu {k:<20} : {v}%")
        # .value_counts(normalize=True) - proportions (entre 0 et 1)
        # .mul(100)                     - conversion en pourcentages
        # .round(1)                     - arrondi à 1 décimale
        # .items()                      - parcourt les paires (valeur, pourcentage)

    if "sexe_cm" in df.columns:
        for k, v in df["sexe_cm"].value_counts(normalize=True).mul(100).round(1).items():
            print(f"    CM {k:<23} : {v}%")

    if "age_cm" in df.columns:
        print(f"    Âge médian CM              : {df['age_cm'].median():.1f} ans")
        print(f"    Âge moyen CM               : {df['age_cm'].mean():.1f} ans")

    taux = df.isnull().mean().mul(100).round(2)
    # df.isnull() - DataFrame de True/False (True = NaN)
    # .mean()     - proportion de NaN par colonne (entre 0 et 1)
    # .mul(100)   - conversion en %

    taux = taux[taux > 0].sort_values(ascending=False)
    # On garde uniquement les colonnes avec au moins un manquant
    # et on trie du plus grand au plus petit taux

    if not taux.empty:
        print("\n  Taux de manquants :")
        for col, tx in taux.items():
            print(f"    {col:<38} : {tx}%")

# ════════════════════════════════════════════════════════════════
# FONCTION - imputer_valeurs_manquantes()
# Imputation automatique selon le type et la distribution
# ════════════════════════════════════════════════════════════════

def imputer_valeurs_manquantes(df: pd.DataFrame,
                                vars_quanti: list,
                                vars_quali: list,
                                log: list) -> pd.DataFrame:
    """
    Impute les valeurs manquantes automatiquement :
    - Variables quantitatives : teste la symétrie (skewness)
        → skewness entre -0.5 et 0.5  : imputation par la MOYENNE
        → skewness hors [-0.5, 0.5]   : imputation par la MÉDIANE
    - Variables qualitatives : imputation par le MODE
    """
    df = df.copy()

    # - VARIABLES QUANTITATIVES -
    print("\n  [Quantitatives]")
    for col in vars_quanti:
        if col not in df.columns:
            print(f"    {col} absente - ignorée")
            continue

        n = df[col].isna().sum()
        if n == 0:
            print(f"   {col} : aucun manquant")
            continue

        # Test de symétrie
        skewness = df[col].skew()

        if -0.5 <= skewness <= 0.5:
            # Distribution symétrique → moyenne
            valeur    = round(df[col].mean(), 2)
            methode   = "Moyenne"
        else:
            # Distribution asymétrique → médiane
            valeur    = df[col].median()
            methode   = "Médiane"

        df[col] = df[col].fillna(valeur)
        log.append({
            "controle": f"Imputation {col}",
            "nb_cas":   n,
            "action":   f"{methode} = {valeur} (skewness = {round(skewness, 3)})"
        })
        print(f"   {col} : {n} NaN | skewness = {round(skewness, 3)} "
              f"→ {methode} = {valeur}")

    # - VARIABLES QUALITATIVES -
    print("\n  [Qualitatives]")
    for col in vars_quali:
        if col not in df.columns:
            print(f"    {col} absente - ignorée")
            continue

        n = df[col].isna().sum()
        if n == 0:
            print(f"   {col} : aucun manquant")
            continue

        mode = df[col].mode()[0]
        # .mode() retourne la/les valeur(s) la/les plus fréquente(s)
        # [0] prend la première en cas d'ex-aequo

        df[col] = df[col].fillna(mode)
        log.append({
            "controle": f"Imputation {col}",
            "nb_cas":   n,
            "action":   f"Mode = '{mode}'"
        })
        print(f"   {col} : {n} NaN → Mode = '{mode}'")

    return df


# ════════════════════════════════════════════════════════════════
# FONCTION — gerer_sauts_questionnaire()
# Remplace les NaN issus des sauts de questions par des modalités
# explicites — ces NaN ne sont pas des erreurs mais des absences
# logiques liées à la structure du questionnaire.
# ════════════════════════════════════════════════════════════════

def gerer_sauts_questionnaire(df: pd.DataFrame, log: list) -> pd.DataFrame:
    """
    Remplace les NaN issus des sauts de questions par des labels explicites :
    - niveau_etude_cm  : NaN → "Non scolarisé"  (CM qui n'a jamais fréquenté l'école)
    - branche_isic_cm  : NaN → "Sans activité"  (CM inactif, question non posée)
    - secteur_instit_cm: NaN → "Sans activité"  (CM inactif, question non posée)
    """
    df = df.copy()

    sauts = {
        "niveau_etude_cm":   "Non scolarisé",
        "branche_isic_cm":   "Sans activité",
        "secteur_instit_cm": "Sans activité",
    }
    # Dictionnaire : colonne → label à attribuer aux NaN
    # Ces labels sont choisis pour être explicites dans les analyses

    for col, label in sauts.items():
        if col not in df.columns:
            print(f"   {col} absente — ignorée")
            continue

        n = df[col].isna().sum()
        if n == 0:
            print(f"  {col} : aucun manquant")
            continue

        df[col] = df[col].fillna(label)
        # fillna(label) : remplace tous les NaN par le label choisi

        log.append({
            "controle": f"Saut questionnaire — {col}",
            "nb_cas":   n,
            "action":   f"NaN → '{label}' (question non posée)"
        })
        print(f" {col} : {n} NaN → '{label}'")

    return df


# ════════════════════════════════════════════════════════════════
# FONCTION PRINCIPALE - main()
# ════════════════════════════════════════════════════════════════

def main():
    section_header("ÉTAPE 3 - NETTOYAGE TABLE MÉNAGE")

    path = OUTPUT_DIR / "labeled" / "hh_labeled.csv"
    if not path.exists():
        raise FileNotFoundError(
            f"Fichier introuvable : {path}\n"
            "- Lancer d'abord : 1_apply_hh_dict.py"
        )
    # Vérification de dépendance : ce fichier ne peut tourner que si
    # l'étape précédente a déjà produit hh_labeled.csv.
    # Message d'erreur clair pour guider l'utilisateur.

    df = pd.read_csv(path, encoding="utf-8-sig")
    # On lit le CSV produit par l'étape 2.
    # encoding="utf-8-sig" : même encodage que celui utilisé pour l'écrire
    # (avec BOM pour compatibilité Excel)

    print(f"\n  Chargé : {len(df):,} ménages × {df.shape[1]} colonnes")

    log = []
    # Liste vide qui va accumuler tous les contrôles effectués.
    # Chaque contrôle = un dictionnaire avec 3 clés :
    # "controle" : nom du contrôle
    # "nb_cas"   : nombre de cas détectés
    # "action"   : ce qu'on a fait (NaN, Signalement...)

    print("\n[Contrôles et corrections]")

    # -- Application des contrôles dans l'ordre --
    df = supprimer_colonnes_parasites(df, log)  # 1. Colonnes inutiles
    df = nettoyer_age_cm(df, log)               # 2. Âges aberrants
    df = nettoyer_taille_menage(df, log)        # 3. Tailles aberrantes
    df = verifier_codes(df, "sexe_cm",                   SEXE_VALIDES,            log)  # 4.
    df = verifier_codes(df, "milieu",                    MILIEU_VALIDES,          log)  # 5.
    df = verifier_codes(df, "statut_emploi_cm",          STATUT_EMPLOI_VALIDES,   log)  # 6.
    df = verifier_codes(df, "situation_matrimoniale_cm", SITUATION_MATRI_VALIDES, log)  # 7.
    df = coherence_sexe_polygamie(df, log)      # 8. Cohérence sexe/mariage
    df = coherence_age_statut(df, log)          # 9. Cohérence âge/emploi
    df = coherence_age_retraite(df, log)        # 10. Cohérence âge/retraite
    df = imputer_valeurs_manquantes(
            df,
            vars_quanti = ["taille_menage", "age_cm"],
            vars_quali  = ["situation_matrimoniale_cm", "sexe_cm", "statut_emploi_cm"],
            log         = log
        )
    df = gerer_sauts_questionnaire(df, log)
    # Note : chaque fonction reçoit df et log, modifie df si nécessaire,
    # ajoute une entrée dans log, et retourne le df modifié.
    # Le df est passé de fonction en fonction comme une chaîne de traitement.

    if not [l for l in log if "aberrant" in l["controle"].lower()
            or "invalide" in l["controle"].lower()]:
        print("  Aucune anomalie majeure détectée.")
    # On vérifie si le log contient des contrôles critiques (aberrant/invalide).
    # Si non - message positif. Les "Signalement" ne comptent pas comme anomalies.

    stats_nettoyage(df)
    # Affiche le résumé statistique final

    # -- Exports --
    save_csv(df, OUTPUT_DIR / "clean" / "hh_clean.csv", label="hh_clean.csv")
    # Table ménage propre - livraison principale de ta partie

    save_csv(pd.DataFrame(log), OUTPUT_DIR / "clean" / "hh_qaqc_log.csv",
             label="hh_qaqc_log.csv")
    # pd.DataFrame(log) : convertit la liste de dictionnaires en DataFrame
    # - chaque dictionnaire devient une ligne du CSV
    # Ce fichier documente toutes les décisions de nettoyage prises.

    print(f"\n  - {len(log)} contrôle(s) dans le log QAQC")


if __name__ == "__main__":
    main()