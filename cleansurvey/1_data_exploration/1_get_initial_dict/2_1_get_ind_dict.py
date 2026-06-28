"""
2_1_get_ind_dict.py
====================
Exploration du fichier individus SPSS (.sav) - Section B du RGPH.

Ce script :
  1. Lit uniquement les METADONNEES du fichier (sans charger toutes les lignes
     en memoire) pour etre rapide meme sur un fichier de plusieurs Go.
  2. Exporte un dictionnaire des variables au format CSV :
     colonne | label_variable | type | n_modalites | modalites (json)
  3. Affiche un apercu (100 premieres lignes) pour verification.

Output :
  output/dict/dict_individus.csv   - dictionnaire complet des variables
  output/dict/apercu_individus.csv - 100 premieres lignes
"""

import sys
import json
import pathlib
import pandas as pd
import pyreadstat

# ── Chemins ──────────────────────────────────────────────────────────────────
ROOT      = pathlib.Path(__file__).resolve().parents[3]
INPUT_SAV = ROOT / "data" / "dixieme_RGPH_5_indiv_SECTION_B.sav"
OUT_DIR   = ROOT / "output" / "dict"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ── 1. Lecture des metadonnees uniquement ─────────────────────────────────────
print("Lecture des metadonnees du fichier SAV ...")
_, meta = pyreadstat.read_sav(
    str(INPUT_SAV),
    metadataonly=True
)

# ── 2. Construction du dictionnaire ───────────────────────────────────────────
print("Construction du dictionnaire des variables ...")
rows = []
for col in meta.column_names:
    idx   = meta.column_names.index(col)
    label = meta.column_labels[idx] if meta.column_labels else ""
    vt    = meta.original_variable_types.get(col, "")
    modalites = meta.variable_value_labels.get(col, {})
    rows.append({
        "variable"       : col,
        "label_variable" : label,
        "type_spss"      : vt,
        "n_modalites"    : len(modalites),
        "modalites"      : json.dumps(modalites, ensure_ascii=False) if modalites else "",
    })

dict_df = pd.DataFrame(rows)
out_dict = OUT_DIR / "dict_individus.csv"
dict_df.to_csv(out_dict, index=False, encoding="utf-8-sig")
print(f"  >> Dictionnaire exporte : {out_dict}  ({len(dict_df)} variables)")

# ── 3. Apercu (100 premieres lignes) ──────────────────────────────────────────
print("Chargement des 100 premieres lignes pour apercu ...")
df_sample, _ = pyreadstat.read_sav(
    str(INPUT_SAV),
    row_limit=100,
    apply_value_formats=False,
)
out_apercu = OUT_DIR / "apercu_individus.csv"
df_sample.to_csv(out_apercu, index=False, encoding="utf-8-sig")
print(f"  >> Apercu exporte : {out_apercu}  ({df_sample.shape})")

# ── 4. Resume console ─────────────────────────────────────────────────────────
print("\n" + "="*60)
print(f"  Nombre total de variables : {len(dict_df)}")
print(f"  Variables avec labels     : {(dict_df['n_modalites'] > 0).sum()}")
print(f"  Colonnes de l apercu      : {list(df_sample.columns)}")
print("="*60)
print("\nDone. Verifiez output/dict/dict_individus.csv")
