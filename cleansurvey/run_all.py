# Script maître d'exécution du pipeline de traitement des données
import os
import sys
import subprocess
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Trouver le chemin de base du projet
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Liste ordonnée des scripts à exécuter
scripts = [
    # 1. Extraction des dictionnaires initiaux (optionnel si déjà générés/remplis)
    os.path.join(BASE_DIR, "1_data_exploration/1_get_initial_dict/1_get_hh_dict.py"),
    os.path.join(BASE_DIR, "1_data_exploration/1_get_initial_dict/2_1_get_ind_dict.py"),
    
    # 2. Application des dictionnaires de variables
    os.path.join(BASE_DIR, "1_data_exploration/2_select_and_label/1_apply_hh_dict.py"),
    os.path.join(BASE_DIR, "1_data_exploration/2_select_and_label/2_1_apply_ind_dict.py"),
    
    # 3. Application des dictionnaires de modalités
    os.path.join(BASE_DIR, "1_data_exploration/2_select_and_label/2_2_apply_ind_dict.py"),
    
    # 4. Nettoyage
    os.path.join(BASE_DIR, "2_clean_and_merge/1_clean_hh_ind.py"),
    
    # 5. Fusion
    os.path.join(BASE_DIR, "2_clean_and_merge/2_merge_hh_ind.py"),
    
    # 6. Rapport QAQC final
    os.path.join(BASE_DIR, "9_qaqc/1_survey_data_qaqc/1_qaqc_report.py")
]

def main():
    logging.info("▶ Lancement du pipeline complet de traitement des données...")
    
    # 0. Nettoyage préalable des anciennes données et rapports
    logging.info("▶ Nettoyage préalable des anciennes données et rapports...")
    import glob
    sys.path.append(BASE_DIR)
    try:
        from config import OUTPUT_DIR, AUX_DIR, QAQC_DIR
        
        # Supprimer les CSV intermédiaires/finaux dans data/
        for f in glob.glob(os.path.join(OUTPUT_DIR, "*.csv")):
            try:
                os.remove(f)
                logging.info(f"  Supprimé : {os.path.basename(f)}")
            except Exception as e:
                logging.warning(f"  Impossible de supprimer {f} : {e}")
                
        # Supprimer les dictionnaires initiaux et remplis dans aux_file/
        for suffix in ["*_init.csv", "*_filled.csv"]:
            for f in glob.glob(os.path.join(AUX_DIR, suffix)):
                try:
                    os.remove(f)
                    logging.info(f"  Supprimé : {os.path.basename(f)}")
                except Exception as e:
                    logging.warning(f"  Impossible de supprimer {f} : {e}")
                    
        # Supprimer les anciens rapports QAQC
        for f in glob.glob(os.path.join(QAQC_DIR, "*")):
            try:
                os.remove(f)
                logging.info(f"  Supprimé : {os.path.basename(f)}")
            except Exception as e:
                logging.warning(f"  Impossible de supprimer {f} : {e}")
    except Exception as e:
        logging.warning(f"⚠️ Erreur lors du nettoyage initial : {e}")
        
    for script in scripts:
        if not os.path.exists(script):
            logging.warning(f"⚠️ Script introuvable : {script} - Étape ignorée.")
            continue
            
        logging.info(f"▶ Exécution de : {os.path.basename(script)}")
        try:
            # Exécuter en tant que sous-processus avec le même interpréteur Python
            result = subprocess.run(
                [sys.executable, script],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            print(result.stdout)
        except subprocess.CalledProcessError as e:
            logging.error(f"❌ Erreur lors de l'exécution de {os.path.basename(script)}:")
            print(e.stderr)
            sys.exit(1)
            
    logging.info("✅ Pipeline exécuté avec succès. Tous les rapports et données nettoyées sont dans le dossier 'data/'.")

if __name__ == "__main__":
    main()
