import sys
import os
import pandas as pd

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from cleansurvey.config import CLEANING_PARAMS, OUTPUT_DIR, NSP_CODES
from cleansurvey.utils import run_cleaning_pipeline

def clean_nsp(df: pd.DataFrame) -> pd.DataFrame:
    """
    Remplace les codes NSP définis dans la configuration par NaN.
    """
    import numpy as np
    robust_nsp = []
    for code in NSP_CODES:
        robust_nsp.append(code)
        try:
            val_float = float(code)
            if val_float.is_integer():
                robust_nsp.append(int(val_float))
                robust_nsp.append(str(int(val_float)))
                robust_nsp.append(f"{int(val_float)}.0")
            robust_nsp.append(str(val_float))
        except ValueError:
            robust_nsp.append(str(code))
            
    robust_nsp = list(set(robust_nsp))
    for col in df.columns:
        df[col] = df[col].replace(robust_nsp, np.nan)
    return df

def main():
    print("--- DEBUT DU NETTOYAGE DES DONNEES ---")
    
    # Charger les bases renommées
    hh_renamed_file = os.path.join(OUTPUT_DIR, "rgph5_hh_renamed.csv")
    ind_renamed_file = os.path.join(OUTPUT_DIR, "rgph5_ind_renamed.csv")
    
    if not os.path.exists(ind_renamed_file):
        print(f"Erreur : La base individus renommée {ind_renamed_file} est introuvable.")
        sys.exit(1)
        
    df_ind = pd.read_csv(ind_renamed_file)
    df_ind = clean_nsp(df_ind)
    
    # Nettoyage Individus
    df_ind_clean = run_cleaning_pipeline(
        df=df_ind,
        params=CLEANING_PARAMS,
        key_cols=["men_id", "numind"],
        label="INDIVIDUS"
    )
    
    # Sauvegarder individus nettoyés
    df_ind_clean.to_csv(os.path.join(OUTPUT_DIR, "rgph5_ind_clean.csv"), index=False, encoding='utf-8')
    
    # Nettoyage Ménages (si présent)
    if os.path.exists(hh_renamed_file):
        df_hh = pd.read_csv(hh_renamed_file)
        df_hh = clean_nsp(df_hh)
        
        df_hh_clean = run_cleaning_pipeline(
            df=df_hh,
            params=CLEANING_PARAMS,
            key_cols=["men_id"],
            label="MENAGES"
        )
        df_hh_clean.to_csv(os.path.join(OUTPUT_DIR, "rgph5_hh_clean.csv"), index=False, encoding='utf-8')
    else:
        print("Base ménages renommée absente. Étape ignorée pour HH.")
        
    print("✔ Nettoyage terminé et bases sauvegardées.")

if __name__ == "__main__":
    main()
