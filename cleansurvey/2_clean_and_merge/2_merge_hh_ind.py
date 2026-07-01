import sys
import os
import pandas as pd

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from cleansurvey.config import CLEANING_PARAMS, OUTPUT_DIR
from cleansurvey.utils import resolve_duplicates

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
