import sys
import os
import pandas as pd

# Ajouter le chemin racine du projet au path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from cleansurvey.config import INPUT_DIR, FILES, AUX_DIR
from cleansurvey.utils import load_sav_metadata

def main():
    print("--- DEBUT EXTRACTION DICTIONNAIRE INDIVIDUS ---")
    file_path = os.path.join(INPUT_DIR, FILES['ind'])
    
    if not os.path.exists(file_path):
        print(f"Erreur : Le fichier brut {file_path} est introuvable.")
        sys.exit(1)
        
    # Extraire les métadonnées
    df_dict = load_sav_metadata(file_path)
    
    # Ajouter les colonnes requises
    df_dict['var_new'] = df_dict['var_orig']
    df_dict['type_new'] = df_dict['type_suggested']
    df_dict['keep'] = 'no'
    
    # Présélectionner les variables requises pour le module Individus du Groupe 2
    target_vars = [
        # Identifiants
        'men_id', 'B01',
        # Géographie
        'A01', 'A02', 'A03', 'A04', 'A10',
        # Démographie
        'B04', 'B06', 'B08', 'B41',
        # Éducation / Scolarisation
        'B29', 'B30', 'B31', 'B32', 'B33', 'B35'
    ]
    
    # Ajouter les variables d'alphabétisation (qui commencent toutes par B34_)
    for var in df_dict['var_orig']:
        if var.startswith('B34_'):
            target_vars.append(var)
            
    df_dict.loc[df_dict['var_orig'].isin(target_vars), 'keep'] = 'yes'
    
    # Sauvegarder
    out_path = os.path.join(AUX_DIR, "dictionary_ind_init.csv")
    df_dict.to_csv(out_path, index=False, encoding='utf-8')
    print(f"✔ Dictionnaire initial individus sauvegardé dans : {out_path}")
    print("Il doit être édité ou copié sous le nom 'dictionary_ind_filled.csv' pour la suite.")

if __name__ == "__main__":
    main()
