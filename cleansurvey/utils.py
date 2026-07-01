# Utilitaires généraux pour le pipeline de traitement des données
import os
import pandas as pd
import numpy as np
import pyreadstat
import logging
from typing import List, Dict, Tuple

# Configuration du logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_sav_metadata(file_path: str) -> pd.DataFrame:
    """
    Lit uniquement les métadonnées d'un fichier .sav (très rapide et économe en mémoire).
    Retourne un DataFrame structuré.
    """
    _, meta = pyreadstat.read_sav(file_path, metadataonly=True)
    
    # Extraire les types des variables
    # Dans pyreadstat, readstat_variable_types est un dictionnaire var_name -> type
    var_types = meta.readstat_variable_types
    
    dict_init = []
    for var in meta.column_names:
        label = meta.column_names_to_labels.get(var, "")
        vtype = var_types.get(var, "unknown")
        
        # Déterminer un type simplifié
        if var in meta.variable_value_labels:
            type_sim = "factor"
        elif vtype in ["double", "float", "numeric", "integer"]:
            type_sim = "numeric"
        else:
            type_sim = "character"
            
        dict_init.append({
            "var_orig": var,
            "label_orig": label,
            "type_orig": vtype,
            "type_suggested": type_sim
        })
        
    return pd.DataFrame(dict_init)

def load_sav_data(file_path: str, columns: List[str] = None) -> Tuple[pd.DataFrame, any]:
    """
    Charge les données d'un fichier .sav, éventuellement filtrées par colonnes
    pour réduire l'empreinte mémoire.
    """
    logging.info(f"Chargement des données de {os.path.basename(file_path)}...")
    df, meta = pyreadstat.read_sav(file_path, usecols=columns)
    logging.info(f"✔ Chargé : {df.shape[0]:,} lignes | {df.shape[1]:,} colonnes")
    return df, meta

def apply_var_dictionary(df: pd.DataFrame, dict_df: pd.DataFrame) -> pd.DataFrame:
    """
    Applique le dictionnaire de variables :
    1. Filtre les variables où keep == 'yes'
    2. Renomme les variables de var_orig vers var_new
    3. Convertit les types selon type_new (numeric, factor, character)
    """
    # Filtrer le dictionnaire
    dict_filtered = dict_df[dict_df['keep'].str.lower() == 'yes'].copy()
    
    # Garder uniquement les colonnes du dictionnaire qui existent dans le df
    existing_vars = [v for v in dict_filtered['var_orig'] if v in df.columns]
    dict_filtered = dict_filtered[dict_filtered['var_orig'].isin(existing_vars)]
    
    # Sélectionner les variables
    df = df[existing_vars].copy()
    
    # Créer le dictionnaire de renommage
    rename_map = dict(zip(dict_filtered['var_orig'], dict_filtered['var_new']))
    df = df.rename(columns=rename_map)
    
    # Appliquer le typage
    for _, row in dict_filtered.iterrows():
        var_name = row['var_new']
        var_type = str(row['type_new']).lower().strip()
        
        if var_name not in df.columns:
            continue
            
        if var_type == 'numeric':
            df[var_name] = pd.to_numeric(df[var_name], errors='coerce')
        elif var_type == 'character':
            df[var_name] = df[var_name].apply(lambda x: str(x).strip() if pd.notna(x) else x)
        elif var_type == 'factor':
            # Garder au format numérique/catégoriel pour l'application ultérieure du dictionnaire de modalités
            df[var_name] = pd.to_numeric(df[var_name], errors='coerce')
            
    logging.info(f"Dictionnaire appliqué : {df.shape[1]} colonnes conservées et renommées.")
    return df

def apply_modality_dictionary(df: pd.DataFrame, dict_df: pd.DataFrame) -> pd.DataFrame:
    """
    Applique le dictionnaire de modalités pour remplacer les codes de catégorie par leurs libellés.
    Le dictionnaire dict_df doit avoir les colonnes : var_name, code, label_new.
    """
    logging.info("Application du dictionnaire de modalités...")
    # Grouper par variable
    vars_in_dict = dict_df['var_name'].unique()
    
    for var in vars_in_dict:
        if var not in df.columns:
            continue
            
        var_dict = dict_df[dict_df['var_name'] == var]
        
        # Créer le dictionnaire de mapping (attention aux types des clés, souvent float ou int)
        mapping = {}
        for _, row in var_dict.iterrows():
            try:
                code_val = float(row['code'])
                # Si c'est un entier représenté en float, on le gère
                if code_val.is_integer():
                    mapping[int(code_val)] = str(row['label_new'])
                mapping[code_val] = str(row['label_new'])
            except ValueError:
                # Si le code n'est pas numérique
                mapping[row['code']] = str(row['label_new'])
                mapping[str(row['code']).strip()] = str(row['label_new'])
        
        # Pour les valeurs manquantes ou non mappées, conserver ou mettre à NaN
        # Optionnel: on applique le mapping
        # On convertit d'abord la colonne pour correspondre au mieux
        df[var] = df[var].map(mapping).fillna(df[var])
        logging.info(f"  Modalités appliquées pour '{var}' : {len(mapping)} catégories mappées.")
        
    return df

def dedup(df: pd.DataFrame, key_cols: List[str]) -> pd.DataFrame:
    """
    Supprime les doublons basés sur les colonnes clés.
    """
    n_before = len(df)
    df = df.drop_duplicates(subset=key_cols, keep='first')
    n_after = len(df)
    n_dup = n_before - n_after
    if n_dup > 0:
        logging.info(f"  [dedup] {n_dup} doublons supprimés sur les clés ({', '.join(key_cols)})")
    else:
        logging.info(f"  [dedup] Aucun doublon sur ({', '.join(key_cols)})")
    return df

def drop_vars(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    """
    Supprime les variables spécifiées et les variables constantes.
    """
    to_drop = [c for c in params.get('vars_to_drop', []) if c in df.columns]
    
    # Identifier les colonnes constantes (un seul élément non nul)
    constant_cols = []
    for col in df.columns:
        if col in key_cols_global:
            continue
        non_na = df[col].dropna()
        if len(non_na.unique()) <= 1:
            constant_cols.append(col)
            
    all_drop = list(set(to_drop + constant_cols))
    if all_drop:
        logging.info(f"  [drop_vars] Suppression de {len(all_drop)} colonnes: {', '.join(all_drop)}")
        df = df.drop(columns=all_drop)
    return df

def normalize_categ(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalise les variables de type chaîne (nettoyage d'espaces).
    """
    char_cols = df.select_dtypes(include=['object']).columns
    for col in char_cols:
        df[col] = df[col].apply(lambda x: ' '.join(str(x).split()) if pd.notna(x) else x)
    if len(char_cols) > 0:
        logging.info(f"  [normalize_categ] Normalisation des espaces sur {len(char_cols)} colonnes de type texte")
    return df

def bound_numeric(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    """
    Applique les bornes numériques. Les valeurs hors bornes sont remplacées par NaN.
    """
    bounds = params.get('numeric_bounds', {})
    report = []
    for var, limit in bounds.items():
        if var in df.columns:
            lo, hi = limit
            df[var] = pd.to_numeric(df[var], errors='coerce')
            n_before = df[var].notna().sum()
            
            # Mettre hors bornes à NaN
            df[var] = np.where((df[var] < lo) | (df[var] > hi), np.nan, df[var])
            
            n_after = df[var].notna().sum()
            n_out = n_before - n_after
            if n_out > 0:
                report.append(f"{var} : {n_out} valeur(s) hors bornes [{lo}, {hi}] -> NaN")
                
    if report:
        logging.info("  [bound_numeric]")
        for r in report:
            logging.info(f"    {r}")
    return df

def apply_consistency_rules(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    """
    Applique les règles de cohérence logique définies dans la configuration.
    """
    rules = params.get('consistency_rules', [])
    for rule in rules:
        label = rule['label']
        cond_str = rule['condition']
        target = rule['target']
        action = rule['action']
        
        if target not in df.columns:
            continue
            
        # Évaluer la condition en créant un masque booléen
        try:
            # Remplacer les opérateurs logiques par les opérateurs pandas si besoin, ou utiliser eval de pandas
            # pandas df.eval() évalue des expressions complexes
            mask = df.eval(cond_str)
            n_flagged = mask.sum()
            
            if n_flagged > 0:
                if action == 'na':
                    df.loc[mask, target] = np.nan
                    logging.info(f"  [consistency] '{label}' : {n_flagged} ligne(s) -> NaN sur {target}")
                else:
                    # Remplacer par une valeur spécifique
                    df.loc[mask, target] = action
                    logging.info(f"  [consistency] '{label}' : {n_flagged} ligne(s) corrigée(s) à '{action}' sur {target}")
        except Exception as e:
            logging.warning(f"  [consistency] Erreur d'évaluation pour la règle '{label}' : {e}")
            
    return df

def impute_numeric(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    """
    Impute les valeurs numériques manquantes.
    """
    strategies = params.get('numeric_impute', {})
    for var, strat in strategies.items():
        if var in df.columns:
            n_na = df[var].isna().sum()
            if n_na == 0 or strat == 'none':
                continue
                
            if strat == 'median':
                fill_val = df[var].median()
            elif strat == 'mean':
                fill_val = df[var].mean()
            elif strat == 'zero':
                fill_val = 0
            else:
                fill_val = np.nan
                
            if not pd.isna(fill_val):
                df[var] = df[var].fillna(fill_val)
                logging.info(f"  [impute_numeric] {var} : {n_na} NA imputées par {strat} ({round(fill_val, 2)})")
    return df

def impute_categ(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    """
    Impute les valeurs catégorielles manquantes.
    """
    strategies = params.get('categ_impute', {})
    for var, strat in strategies.items():
        if var in df.columns:
            n_na = df[var].isna().sum()
            if n_na == 0 or strat == 'none':
                continue
                
            if strat == 'mode':
                mode_series = df[var].mode()
                fill_val = mode_series.iloc[0] if not mode_series.empty else 'Unknown'
            else:
                fill_val = strat
                
            df[var] = df[var].fillna(fill_val)
            logging.info(f"  [impute_categ] {var} : {n_na} NA imputées par '{fill_val}'")
    return df

# Variable globale pour garder la trace des clés primaires lors de la suppression des constantes
key_cols_global = []

def run_cleaning_pipeline(df: pd.DataFrame, params: dict, key_cols: List[str], label: str = "") -> pd.DataFrame:
    """
    Orchestre tout le pipeline de nettoyage.
    """
    global key_cols_global
    key_cols_global = key_cols
    
    logging.info(f"\n============================================================")
    logging.info(f"Nettoyage : {label} ({df.shape[0]:,} lignes x {df.shape[1]} colonnes)")
    logging.info(f"============================================================")
    
    df = dedup(df, key_cols)
    df = drop_vars(df, params)
    df = normalize_categ(df)
    df = bound_numeric(df, params)
    df = apply_consistency_rules(df, params)
    df = impute_numeric(df, params)
    df = impute_categ(df, params)
    
    logging.info(f"Résultat final {label} : {df.shape[0]:,} lignes x {df.shape[1]} colonnes\n")
    return df

def resolve_duplicates(df_hh: pd.DataFrame, df_ind: pd.DataFrame, params: dict) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Résout les doublons de colonnes entre HH et IND.
    """
    strategies = params.get('duplicate_cols_strategy', {})
    suffixes = params.get('suffixes', ('_hh', '_ind'))
    
    common_cols = set(df_hh.columns).intersection(set(df_ind.columns))
    # Ne pas considérer la clé de jointure commune
    join_key = 'men_id'
    common_cols.discard(join_key)
    common_cols.discard('numind') # clé secondaire
    
    for col in common_cols:
        strat = strategies.get(col, 'both')
        if strat == 'hh':
            df_ind = df_ind.drop(columns=[col])
            logging.info(f"  [duplicates] '{col}' : version HH conservée, version IND supprimée")
        elif strat == 'ind':
            df_hh = df_hh.drop(columns=[col])
            logging.info(f"  [duplicates] '{col}' : version IND conservée, version HH supprimée")
        elif strat == 'both':
            df_hh = df_hh.rename(columns={col: f"{col}{suffixes[0]}"})
            df_ind = df_ind.rename(columns={col: f"{col}{suffixes[1]}"})
            logging.info(f"  [duplicates] '{col}' : renommée en '{col}{suffixes[0]}' (HH) et '{col}{suffixes[1]}' (IND)")
            
    return df_hh, df_ind

def section_header(titre: str) -> None:
    """Affiche un séparateur de section dans la console."""
    print(f"\n{'=' * 55}")
    # '=' * 55 - répète le caractère '=' 55 fois
    # Produit : =======================================================
    print(f"  {titre}")
    print(f"{'=' * 55}")