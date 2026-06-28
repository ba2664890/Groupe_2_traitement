"""
2_1_apply_ind_dict.py
======================
Etape 2 du pipeline individus :
  - Selectionne les variables pertinentes depuis le fichier .sav brut
  - Renomme selon config.IND_RENAME
  - Applique les labels SPSS comme valeurs lisibles
  - Exporte un fichier intermediaire individus_selected.csv

Output : output/individus_selected.csv
"""

import sys
import pathlib

# Ajout du dossier cleansurvey au path pour importer config et utils
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

import config
from utils import load_sav, select_and_rename

def main():
    print("="*60)
    print("ETAPE 2 : Selection et renommage des variables individus")
    print("="*60)

    # Colonnes a charger (brutes)
    cols_brutes = list(config.IND_RENAME.keys())

    # Chargement (sans labels SPSS pour garder les codes numeriques)
    df, meta = load_sav(
        config.IND_SAV,
        apply_formats=False,
        cols=cols_brutes,
    )

    print(f"  Lignes chargees     : {len(df):,}")
    print(f"  Colonnes selectionnees : {df.shape[1]}")

    # Renommage
    df = select_and_rename(df, config.IND_RENAME, keep_unmapped=False)
    print(f"  Colonnes apres renommage : {list(df.columns)}")

    # Export intermediaire
    out = config.OUTPUT_DIR / "individus_selected.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False, encoding="utf-8-sig")
    print(f"  >> Fichier intermediaire : {out}")
    print("="*60)

if __name__ == "__main__":
    main()
