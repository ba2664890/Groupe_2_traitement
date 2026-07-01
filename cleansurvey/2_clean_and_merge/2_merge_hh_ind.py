import sys
import os
import pandas as pd
import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from cleansurvey.config import CLEANING_PARAMS, OUTPUT_DIR
from cleansurvey.utils import resolve_duplicates

def calculer_agregats(df_ind: pd.DataFrame) -> list:
    """Calcule des indicateurs démographiques agrégés au niveau ménage."""
    agg_list = []

    # - AGRÉGAT 1 : Nombre d'enfants de moins de 5 ans -
    if "age" in df_ind.columns:
        agg_list.append(
            df_ind[df_ind["age"] < 5]
            .groupby("men_id").size()
            .reset_index(name="nb_enfants_moins5ans")
        )

    # - AGRÉGAT 2 : Nombre de femmes en âge de procréer (15-49 ans) -
    if "age" in df_ind.columns and "sexe" in df_ind.columns:
        agg_list.append(
            df_ind[
                df_ind["sexe"].isin(["Féminin", 2])
                & df_ind["age"].between(15, 49)
            ]
            .groupby("men_id").size()
            .reset_index(name="nb_femmes_15_49")
        )

    # - AGRÉGAT 3 : Ratio de dépendance démographique -
    if "age" in df_ind.columns:
        tmp = df_ind.copy()
        tmp["dep"] = tmp["age"].apply(
            lambda a: 1 if pd.notna(a) and (a < 15 or a >= 65)
                      else (0 if pd.notna(a) else np.nan)
        )
        tmp["actif"] = tmp["age"].apply(
            lambda a: 1 if pd.notna(a) and 15 <= a < 65
                      else (0 if pd.notna(a) else np.nan)
        )

        ratio = (
            tmp.groupby("men_id")
            .apply(
                lambda g: round(g["dep"].sum() / g["actif"].sum(), 3)
                          if g["actif"].sum() > 0 else np.nan,
                include_groups=False
            )
            .reset_index(name="ratio_dependance")
        )
        agg_list.append(ratio)

    return agg_list

def main():
    print("--- DEBUT DE LA FUSION MENAGES ET INDIVIDUS ---")
    
    hh_clean_file = os.path.join(OUTPUT_DIR, "rgph5_hh_clean.csv")
    ind_clean_file = os.path.join(OUTPUT_DIR, "rgph5_ind_clean.csv")
    
    if not os.path.exists(ind_clean_file):
        print(f"Erreur : La base individus nettoyée {ind_clean_file} est introuvable.")
        sys.exit(1)
        
    df_ind = pd.read_csv(ind_clean_file)
    
    if os.path.exists(hh_clean_file):
        df_hh = pd.read_csv(hh_clean_file)
        
        n_hh_before = len(df_hh)
        n_ind_before = len(df_ind)
        
        # ----------------------------------------------------
        # 1. Génération de la base MENAGES finale (hh_final.csv)
        # ----------------------------------------------------
        print("💡 Calcul et intégration des agrégats pour la table ménages finale...")
        df_hh_final = df_hh.copy()
        for df_agg in calculer_agregats(df_ind):
            col = df_agg.columns[-1]
            df_hh_final = df_hh_final.merge(df_agg, on="men_id", how="left")
            df_hh_final[col] = df_hh_final[col].fillna(0)
            
        hh_final_file = os.path.join(OUTPUT_DIR, "hh_final.csv")
        df_hh_final.to_csv(hh_final_file, index=False, encoding='utf-8-sig')
        print(f"✔ Base ménages finale sauvegardée dans : {hh_final_file}")
        
        # ----------------------------------------------------
        # 2. Génération de la base INDIVIDUS fusionnée (rgph5_merged.csv)
        # ----------------------------------------------------
        # Résoudre les colonnes dupliquées
        df_hh_res, df_ind_res = resolve_duplicates(df_hh, df_ind, CLEANING_PARAMS)
        
        # Jointure gauche (IND est le pivot)
        df_merged = pd.merge(df_ind_res, df_hh_res, on="men_id", how="left")
        
        print(f"  [merge] Jointure left sur 'men_id'")
        print(f"  [merge] Ménages : {n_hh_before:,} lignes")
        print(f"  [merge] Individus : {n_ind_before:,} lignes")
        print(f"  [merge] Résultat : {len(df_merged):,} lignes x {df_merged.shape[1]} colonnes")
        
        # Réordonner les colonnes pour mettre les identifiants en premier
        id_cols = ['men_id', 'numind']
        other_cols = [c for c in df_merged.columns if c not in id_cols]
        col_order = id_cols + other_cols
        df_merged = df_merged[col_order]
        
    else:
        print("Base ménages nettoyée absente. La base fusionnée sera identique à la base individus.")
        df_merged = df_ind
        
    # Sauvegarder la base fusionnée finale
    out_file = os.path.join(OUTPUT_DIR, "rgph5_merged.csv")
    df_merged.to_csv(out_file, index=False, encoding='utf-8')
    print(f"✔ Base fusionnée sauvegardée dans : {out_file}")

if __name__ == "__main__":
    main()
