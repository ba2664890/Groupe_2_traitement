"""
diagnostic.py — Identifier la vraie clé ménage dans les données
"""
import sys
sys.path.insert(0, '.')

from utils import read_sav
from config import FILE_INDIV, FILE_HABITAT

print("=" * 55)
print("  DIAGNOSTIC — CLÉ MÉNAGE")
print("=" * 55)

# -- Section B (individus) --
print("\n[Section B — Individus]")
df_b = read_sav(FILE_INDIV)

cols_a = [c for c in df_b.columns if c.startswith('A')]
print(f"\nColonnes A* disponibles : {cols_a}")

for col in cols_a:
    print(f"  {col} → {df_b[col].nunique()} valeurs uniques | exemple : {df_b[col].dropna().iloc[0]}")

print(f"\nTotal lignes Section B : {len(df_b):,}")

# -- Section E (habitat) --
print("\n[Section E — Habitat]")
df_e = read_sav(FILE_HABITAT)

cols_a_e = [c for c in df_e.columns if c.startswith('A')]
print(f"\nColonnes A* disponibles : {cols_a_e}")

for col in cols_a_e:
    print(f"  {col} → {df_e[col].nunique()} valeurs uniques | exemple : {df_e[col].dropna().iloc[0]}")

print(f"\nTotal lignes Section E : {len(df_e):,}")

# -- Test combinaisons de clés --
print("\n[Test combinaisons de clés]")
combos = [
    ["A09"],
    ["A01", "A09"],
    ["A01", "A02", "A09"],
    ["A01", "A02", "A05", "A09"],
    ["A01", "A02", "A06", "A09"],
    ["A01", "A02", "A04", "A09"],
]

for combo in combos:
    cols_dispo = [c for c in combo if c in df_b.columns]
    if len(cols_dispo) == len(combo):
        n = df_b[cols_dispo].drop_duplicates().shape[0]
        print(f"  {'+'.join(combo)} → {n:,} ménages uniques dans Section B")
    else:
        print(f"  {'+'.join(combo)} → colonnes manquantes : {set(combo)-set(df_b.columns)}")

print("\nDiagnostic terminé.")
