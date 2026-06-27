"""
run_all.py — Lance le pipeline ménage complet dans l'ordre
==========================================================
Usage : python run_all.py

Étapes :
  1. Dictionnaire des variables ménage
  2. Sélection & étiquetage
  3. Nettoyage + imputation
  4. Fusion finale
  5. Rapport QAQC
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from utils import section_header
import importlib.util


def run_module(path: str, label: str):
    """Importe et exécute le main() d'un module."""
    spec = importlib.util.spec_from_file_location("module", path)
    mod  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.main()


BASE = Path(__file__).resolve().parent

if __name__ == "__main__":
    print("\n" + "=" * 55)
    print("  PIPELINE MÉNAGE — Groupe 2 RGPH-5")
    print("=" * 55)

    steps = [
        (BASE / "1_data_exploration/1_get_initial_dict/1_get_hh_dict.py",
         "Dictionnaire variables ménage"),

        (BASE / "1_data_exploration/2_select_and_label/1_apply_hh_dict.py",
         "Sélection & étiquetage"),

        (BASE / "2_clean_and_merge/1_clean_hh_ind.py",
         "Nettoyage + imputation table ménage"),

        (BASE / "2_clean_and_merge/2_merge_hh_ind.py",
         "Fusion table ménage finale"),

        (BASE / "2_clean_and_merge/3_qaqc_menage.py",
         "Rapport QAQC"),
    ]

    for path, label in steps:
        run_module(str(path), label)

    print("\n" + "=" * 55)
    print("  PIPELINE MÉNAGE TERMINÉ")
    print("=" * 55 + "\n")