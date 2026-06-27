"""
2_clean_and_merge/2_merge_hh_ind.py
=====================================
Étape 4 - Construction de la table ménage finale.

Source  : output/clean/hh_clean.csv
          output/clean/ind_clean.csv  (optionnel - produit par les collègues)
Output  : output/final/hh_final.csv
"""
# Ce fichier est la DERNIÈRE étape du pipeline ménage.
# Il prend la table ménage propre (hh_clean.csv) et l'enrichit
# avec des indicateurs démographiques calculés depuis la table individus.
#
# IMPORTANT : ind_clean.csv est produit par les COLLÈGUES (partie individus).
# Si ce fichier n'existe pas encore, le pipeline tourne quand même
# en "mode dégradé" : on exporte hh_clean.csv tel quel sous le nom hh_final.csv.
# Dès que les collègues livrent ind_clean.csv, on relance ce script.


# - IMPORTS ---------------------------

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
# Remonte d'un niveau vers cleansurvey/ pour trouver config.py et utils.py

import pandas as pd
import numpy as np

from config import OUTPUT_DIR
# On n'a besoin que de OUTPUT_DIR ici - ce script ne lit pas les .sav,
# il travaille uniquement sur les CSV déjà produits.

from utils import save_csv, section_header


# ════════════════════════════════════════════════════════════════
# FONCTION 1 - calculer_agregats()
# Calculer des indicateurs démographiques au niveau ménage
# depuis la table individus
# ════════════════════════════════════════════════════════════════

def calculer_agregats(df_ind: pd.DataFrame) -> list:
    """Calcule des indicateurs démographiques agrégés au niveau ménage."""

    agg_list = []
    # Liste qui va contenir plusieurs petits DataFrames d'agrégats.
    # Chaque agrégat = une nouvelle colonne à ajouter à la table ménage.


    # - AGRÉGAT 1 : Nombre d'enfants de moins de 5 ans -

    if "age" in df_ind.columns:
        agg_list.append(
            df_ind[df_ind["age"] < 5]
            # Filtre : ne garde que les individus âgés de moins de 5 ans

            .groupby(["A06", "A09"]).size()
            # Regroupe par ménage (A06+A09) et compte le nombre d'enfants

            .reset_index(name="nb_enfants_moins5ans")
            # Transforme en DataFrame avec la colonne nb_enfants_moins5ans
        )
        # Résultat : une ligne par ménage avec le nb d'enfants < 5 ans
        # Indicateur utile pour les politiques de santé infantile et nutrition


    # - AGRÉGAT 2 : Nombre de femmes en âge de procréer (15-49 ans) -

    if "age" in df_ind.columns and "sexe" in df_ind.columns:
        agg_list.append(
            df_ind[
                df_ind["sexe"].isin(["Féminin", 2])
                # .isin() : accepte "Féminin" (si déjà étiqueté)
                # OU 2 (si encore en code numérique)
                # - robuste peu importe l'état de la table individus

                & df_ind["age"].between(15, 49)
                # .between(15, 49) = âge >= 15 ET âge <= 49
                # Définition standard OMS des femmes en âge de procréer
            ]
            .groupby(["A06", "A09"]).size()
            .reset_index(name="nb_femmes_15_49")
        )
        # Indicateur clé pour les études de fécondité et planification familiale


    # - AGRÉGAT 3 : Ratio de dépendance démographique -

    if "age" in df_ind.columns:
        tmp = df_ind.copy()
        # On travaille sur une copie pour ne pas modifier df_ind

        tmp["dep"] = tmp["age"].apply(
            lambda a: 1 if pd.notna(a) and (a < 15 or a >= 65)
                      else (0 if pd.notna(a) else np.nan)
        )
        # lambda = fonction anonyme rapide, équivalent de :
        # def classer_dependant(a):
        #     if pd.notna(a) and (a < 15 or a >= 65): return 1  # dépendant
        #     elif pd.notna(a): return 0                         # actif
        #     else: return np.nan                                 # inconnu
        #
        # Dépendants = enfants (< 15 ans) + personnes âgées (>= 65 ans)
        # Ce sont les personnes qui "dépendent" économiquement des actifs

        tmp["actif"] = tmp["age"].apply(
            lambda a: 1 if pd.notna(a) and 15 <= a < 65
                      else (0 if pd.notna(a) else np.nan)
        )
        # Actifs = population en âge de travailler (15 à 64 ans)

        ratio = (
            tmp.groupby(["A06", "A09"])
            .apply(
                lambda g: round(g["dep"].sum() / g["actif"].sum(), 3)
                          if g["actif"].sum() > 0 else np.nan,
                include_groups=False
                # Pour chaque ménage (groupe g) :
                # ratio = nb dépendants / nb actifs
                # Ex : 4 dépendants / 2 actifs = ratio de 2.0
                # Si aucun actif dans le ménage - NaN (évite division par 0)
                # include_groups=False : nouvelle syntaxe pandas 2.0
            )
            .reset_index(name="ratio_dependance")
        )
        agg_list.append(ratio)
        # Ratio élevé - beaucoup de dépendants pour peu d'actifs = ménage vulnérable
        # Ratio faible - beaucoup d'actifs = ménage plus autonome économiquement

    return agg_list
    # Retourne une liste de 3 DataFrames :
    # [df_enfants_moins5, df_femmes_1549, df_ratio_dependance]


# ════════════════════════════════════════════════════════════════
# FONCTION PRINCIPALE - main()
# ════════════════════════════════════════════════════════════════

def main():
    section_header("ÉTAPE 4 - FUSION TABLE MÉNAGE FINALE")

    # - Chargement de la table ménage propre -
    hh_path = OUTPUT_DIR / "clean" / "hh_clean.csv"
    if not hh_path.exists():
        raise FileNotFoundError(
            f"Introuvable : {hh_path}\n- Lancer d'abord 1_clean_hh_ind.py"
        )
    # Vérification de dépendance : hh_clean.csv doit exister
    # (produit par l'étape 3)

    df_hh = pd.read_csv(hh_path, encoding="utf-8-sig")
    print(f"\n  Table ménage chargée : {len(df_hh):,} lignes")

    # - Chargement de la table individus (optionnelle) -
    ind_path = OUTPUT_DIR / "clean" / "ind_clean.csv"
    df_final = df_hh.copy()
    # Par défaut, df_final = copie de hh_clean.
    # Si ind_clean.csv existe, on l'enrichira.
    # Sinon, df_final reste tel quel - "mode dégradé"

    if ind_path.exists():
        # - Mode complet : ind_clean.csv disponible -
        df_ind = pd.read_csv(ind_path, encoding="utf-8-sig")
        print(f"  Table individus chargée : {len(df_ind):,} lignes")

        print("\n[Calcul des agrégats individus]")
        for df_agg in calculer_agregats(df_ind):
            # On parcourt les 3 DataFrames d'agrégats retournés

            col = df_agg.columns[-1]
            # .columns[-1] = dernière colonne du DataFrame d'agrégat
            # = le nom de l'indicateur calculé
            # Ex : "nb_enfants_moins5ans", "nb_femmes_15_49", "ratio_dependance"

            df_final = df_final.merge(df_agg, on=["A06", "A09"], how="left")
            # Jointure gauche sur la clé ménage A06+A09 :
            # on ajoute la colonne d'agrégat à la table ménage.
            # how="left" - tous les ménages sont conservés,
            # même ceux sans individus correspondants (NaN alors)

            df_final[col] = df_final[col].fillna(0)
            # Les ménages sans enfants < 5 ans auront NaN après le merge.
            # .fillna(0) - remplace NaN par 0 (absence = zéro enfant)
            # Logique : si aucun individu < 5 ans trouvé pour ce ménage,
            # c'est bien qu'il y en a 0, pas que c'est inconnu.

            print(f"  {col} ajouté")

    else:
        # - Mode dégradé : ind_clean.csv absent -
        print(f"  Table individus absente - export ménage seul")
        # On continue sans les agrégats.
        # df_final = hh_clean.csv sans enrichissement.
        # À relancer dès que les collègues livrent ind_clean.csv.

    # - Affichage des colonnes finales -
    print(f"\n  - Table finale : {len(df_final):,} ménages × {df_final.shape[1]} colonnes")
    print("\n  Colonnes :")
    for col in df_final.columns:
        print(f"     {col}")
    # Liste exhaustive de toutes les colonnes - permet de vérifier
    # visuellement que la table est complète et propre

    # - Export final -
    save_csv(df_final, OUTPUT_DIR / "final" / "hh_final.csv", label="hh_final.csv")



if __name__ == "__main__":
    main()