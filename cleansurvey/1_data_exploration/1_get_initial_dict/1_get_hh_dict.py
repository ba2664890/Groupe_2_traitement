import sys
import os
import pandas as pd

# Ajouter le chemin racine du projet au path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from cleansurvey.config import INPUT_DIR, FILES, AUX_DIR
from cleansurvey.utils import load_sav_metadata

def main():
    print("--- DEBUT EXTRACTION DICTIONNAIRE MENAGES (HABITAT) ---")
    file_path = os.path.join(INPUT_DIR, FILES['hh'])
    
    if not os.path.exists(file_path):
        print(f"Erreur : Le fichier brut {file_path} est introuvable.")
        sys.exit(1)
        
    # Extraire les métadonnées
    df_dict = load_sav_metadata(file_path)
    
    # Ajouter les colonnes requises pour la phase d'application du dictionnaire
    df_dict['var_new'] = df_dict['var_orig']
    df_dict['type_new'] = df_dict['type_suggested']
    df_dict['keep'] = 'no' # Par défaut, on ne garde pas, l'utilisateur choisira 'yes'
    
    # Pour certaines variables géographiques connues, on met à 'yes'
    geo_vars = ['men_id', 'A01', 'A02', 'A03', 'A04', 'A10']
    df_dict.loc[df_dict['var_orig'].isin(geo_vars), 'keep'] = 'yes'
    
    # Sauvegarder
    out_path = os.path.join(AUX_DIR, "dictionary_hh_init.csv")
    df_dict.to_csv(out_path, index=False, encoding='utf-8')
    print(f"✔ Dictionnaire initial ménages sauvegardé dans : {out_path}")
    print("Il doit être édité ou copié sous le nom 'dictionary_hh_filled.csv' pour la suite.")

if __name__ == "__main__":
    main()
