"""
run_all.py
===========
Orchestrateur du pipeline individus RGPH.

Execute les etapes dans l'ordre :
  1. Exploration et dictionnaire des variables
  2. Selection et renommage
  3. Nettoyage, derivation et QAQC

Usage :
    python cleansurvey/run_all.py
    python cleansurvey/run_all.py --steps 2 3   # executer seulement les etapes 2 et 3
    python cleansurvey/run_all.py --skip-explore  # sauter l'exploration si dict deja fait
"""

import sys
import time
import argparse
import pathlib
import traceback

# Path
ROOT       = pathlib.Path(__file__).resolve().parent.parent
SCRIPT_DIR = pathlib.Path(__file__).resolve().parent

sys.path.insert(0, str(SCRIPT_DIR))

STEPS = {
    1: {
        "nom"    : "Exploration et dictionnaire",
        "module" : "1_data_exploration.1_get_initial_dict.2_1_get_ind_dict",
        "func"   : None,
    },
    2: {
        "nom"    : "Selection et renommage des variables",
        "module" : "1_data_exploration.2_select_and_label.2_1_apply_ind_dict",
        "func"   : "main",
    },
    3: {
        "nom"    : "Nettoyage, derivation et QAQC",
        "module" : "2_clean_and_merge.1_clean_hh_ind",
        "func"   : "main",
    },
}


def run_step(step_id: int):
    """Execute une etape du pipeline."""
    step = STEPS[step_id]
    print(f"\n{'='*60}")
    print(f"  ETAPE {step_id} : {step['nom']}")
    print(f"{'='*60}")
    t0 = time.time()

    try:
        import importlib
        mod = importlib.import_module(step["module"].replace(".", ".").replace("1_data_exploration.", "1_data_exploration.").replace("2_clean_and_merge.", "2_clean_and_merge."))
        if step["func"]:
            getattr(mod, step["func"])()
        else:
            pass  # Le module s'execute a l'import (script autonome)

        duree = round(time.time() - t0, 1)
        print(f"\n  [OK] Etape {step_id} terminee en {duree}s")
        return True

    except Exception as e:
        print(f"\n  [ERREUR] Etape {step_id} : {e}")
        traceback.print_exc()
        return False


def main():
    parser = argparse.ArgumentParser(description="Pipeline individus RGPH")
    parser.add_argument(
        "--steps", nargs="+", type=int, default=[1, 2, 3],
        help="Etapes a executer (1=explore, 2=select, 3=clean)"
    )
    parser.add_argument(
        "--skip-explore", action="store_true",
        help="Sauter l'etape d'exploration (si dict deja produit)"
    )
    args = parser.parse_args()

    steps_a_executer = args.steps
    if args.skip_explore and 1 in steps_a_executer:
        steps_a_executer = [s for s in steps_a_executer if s != 1]

    print("=" * 60)
    print("  PIPELINE INDIVIDUS - 10eme RGPH Senegal")
    print("  Modules : Demographiques, Geographiques, Education")
    print(f"  Etapes planifiees : {steps_a_executer}")
    print("=" * 60)

    t_global = time.time()
    succes = []
    echecs = []

    for step_id in sorted(steps_a_executer):
        if step_id not in STEPS:
            print(f"  [WARN] Etape {step_id} inconnue, ignoree.")
            continue
        ok = run_step(step_id)
        if ok:
            succes.append(step_id)
        else:
            echecs.append(step_id)
            print(f"  [STOP] Arret apres echec de l'etape {step_id}")
            break

    duree_totale = round(time.time() - t_global, 1)
    print(f"\n{'='*60}")
    print(f"  BILAN : {len(succes)} etape(s) reussie(s), {len(echecs)} echec(s)")
    print(f"  Duree totale : {duree_totale}s")
    if echecs:
        print(f"  Etapes en echec : {echecs}")
    else:
        print("  Pipeline termine avec succes !")
    print("=" * 60)


if __name__ == "__main__":
    main()
