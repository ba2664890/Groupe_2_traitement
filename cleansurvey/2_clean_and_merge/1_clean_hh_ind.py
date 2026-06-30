"""
1_clean_hh_ind.py
==================
Etape 3 du pipeline individus (votre partie : demo, geo, education) :

  1. Charge le fichier intermediaire individus_selected.csv
  2. Traite les valeurs manquantes (codes -> NaN + flags)
  3. Traite les valeurs aberrantes (hors plage -> NaN + flags)
  4. Recode les modalites (codes numeriques -> etiquettes)
  5. Derive les variables calculees :
     - groupe_age (tranches d'age quinquennales)
     - niveau_etudes_groupe (regroupement des classes en niveaux)
     - alphabetise (1 = alphabetise dans au moins une langue)
  6. Controles de coherence
  7. Exporte individus_clean.csv
  8. Genere QAQC_individus.xlsx

Usage :
    python cleansurvey/2_clean_and_merge/1_clean_hh_ind.py
"""

import sys
import pathlib
import numpy as np
import pandas as pd

# Ajout du dossier cleansurvey au path
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import config
from utils import (
    flag_and_nullify_missing,
    flag_outliers,
    missing_summary,
    outlier_summary,
    apply_recodings,
    compute_groupe_age,
    compute_alphabetisation,
    run_coherence_checks,
    compute_all_distributions,
    generate_qaqc,
)


# ==============================================================================
# ETAPE A : Chargement
# ==============================================================================
def load_selected():
    """Charge le fichier intermediaire selectionne."""
    csv_path = config.OUTPUT_DIR / "individus_selected.csv"

    # Fallback : si le CSV n'existe pas encore, charger directement le .sav
    if not csv_path.exists():
        print("  [INFO] individus_selected.csv absent, chargement direct du .sav ...")
        from utils import load_sav
        df, _ = load_sav(
            config.IND_SAV,
            apply_formats=False,
            cols=list(config.IND_RENAME.keys()),
        )
        from utils import select_and_rename
        df = select_and_rename(df, config.IND_RENAME, keep_unmapped=False)
    else:
        print(f"  Chargement de {csv_path.name} ...")
        df = pd.read_csv(csv_path, encoding="utf-8-sig", low_memory=False)

    n_raw = len(df)
    print(f"  >> {n_raw:,} individus charges, {df.shape[1]} variables")
    return df, n_raw


# ==============================================================================
# ETAPE B : Traitement des manquants
# ==============================================================================
def traiter_manquants(df: pd.DataFrame) -> pd.DataFrame:
    print("\n[B] Traitement des valeurs manquantes ...")
    df = flag_and_nullify_missing(df, config.MISSING_CODES)
    n_miss_total = df[[c for c in df.columns if not c.endswith("_flag_miss")]].isna().sum().sum()
    print(f"  >> {n_miss_total:,} valeurs manquantes apres traitement")
    return df


# ==============================================================================
# ETAPE C : Traitement des aberrants
# ==============================================================================
def traiter_aberrants(df: pd.DataFrame) -> pd.DataFrame:
    print("\n[C] Detection et traitement des valeurs aberrantes ...")
    df = flag_outliers(df, config.VALID_RANGES, action="nullify")

    # Rapport rapide
    for col, (vmin, vmax) in config.VALID_RANGES.items():
        flag_col = col + "_flag_outlier"
        if flag_col in df.columns:
            n = int(df[flag_col].sum())
            if n > 0:
                print(f"  [WARN] {col} : {n} valeurs hors plage [{vmin}-{vmax}] => mises a NaN")
    return df


# ==============================================================================
# ETAPE D : Recodage des modalites
# ==============================================================================
def recoder(df: pd.DataFrame) -> pd.DataFrame:
    print("\n[D] Recodage des modalites ...")

    # Recodages standards
    df = apply_recodings(df, config.RECODINGS)

    # Niveau d'etudes : B32 (classe) -> groupe niveau
    if "niveau_etudes" in df.columns:
        df["niveau_etudes_groupe"] = df["niveau_etudes"].map(config.RECODE_NIVEAU_ETUDES)
        # Personnes jamais scolarisees (B29 = 0) -> "Aucun"
        if "scolarise" in df.columns:
            mask_jamais = df["scolarise"].isna() | (df["scolarise"] == 0.0)
            df.loc[mask_jamais & df["niveau_etudes_groupe"].isna(), "niveau_etudes_groupe"] = "Aucun"

    # Recoder la variable scolarise (apres avoir utilise le code brut)
    if "scolarise" in df.columns:
        df["scolarise"] = df["scolarise"].map(config.RECODE_SCOLARISE)

    print("  >> Recodage termine")
    return df


# ==============================================================================
# ETAPE E : Derivation des variables calculees
# ==============================================================================
def deriver_variables(df: pd.DataFrame) -> pd.DataFrame:
    print("\n[E] Derivation des variables calculees ...")

    # E1. Groupes d'age
    df = compute_groupe_age(df, "age", config.AGE_BINS, config.AGE_LABELS)
    print(f"  >> groupe_age cree : {df['groupe_age'].value_counts().sum():,} non-NaN")

    # E2. Alphabetisation globale (au moins une langue)
    alpha_cols_norm_present = [c for c in config.ALPHA_COLS_NORM if c in df.columns]
    df = compute_alphabetisation(
        df,
        alpha_cols=alpha_cols_norm_present,
        alpha_oui_code=config.ALPHA_OUI_CODE,
        out_col="alphabetise",
    )
    n_alpha = int(df["alphabetise"].sum()) if "alphabetise" in df.columns else 0
    n_total = len(df)
    pct = round(100 * n_alpha / n_total, 1) if n_total > 0 else 0
    print(f"  >> alphabetise : {n_alpha:,} ({pct}%) alphabetises dans au moins 1 langue")

    # E3. Indicateur scolarisation actuelle
    if "scolarise" in df.columns:
        df["actuellement_scolarise"] = (df["scolarise"] == "Actuellement scolarise").astype(int)

    # E4. Taux d'alphabetisation par langue (colonne "pct" calculee au QAQC)
    # Les colonnes alpha_* sont deja presentes (0/1)

    return df


# ==============================================================================
# ETAPE F : Controles de coherence
# ==============================================================================
def controler_coherence(df: pd.DataFrame) -> pd.DataFrame:
    print("\n[F] Controles de coherence ...")

    # Controle 1 : un seul CM par menage
    if "lien_cm" in df.columns and "id_menage" in df.columns:
        n_cm_par_menage = df[df["lien_cm"] == "Chef de menage"].groupby("id_menage").size()
        n_menages_multi_cm = int((n_cm_par_menage > 1).sum())
        print(f"  Controle CM unique par menage : {n_menages_multi_cm} menages avec >1 CM")

    # Controle 2 : age < 3 et actuellement scolarise
    if "age" in df.columns and "scolarise" in df.columns:
        mask = (df["age"] < 3) & (df["scolarise"] == "Actuellement scolarise")
        n = int(mask.sum())
        print(f"  Controle age/scolarisation    : {n} individus < 3 ans declares scolarises")

    # Controle 3 : age < 10 et maries
    if "age" in df.columns and "situation_matrim" in df.columns:
        maries = ["Marie(e) monogame", "Marie(e) polygame 1ere epouse",
                  "Marie(e) polygame autre epouse", "Union libre"]
        mask = (df["age"] < 10) & df["situation_matrim"].isin(maries)
        n = int(mask.sum())
        if n > 0:
            print(f"  [ALERTE] age/mariage : {n} individus < 10 ans declares maries (a verifier)")
        else:
            print(f"  Controle age/mariage : OK (0 violation)")

    return df


# ==============================================================================
# ETAPE G : Calcul des estimations primaires (pour le QAQC)
# ==============================================================================
def calcul_estimations(df: pd.DataFrame) -> pd.DataFrame:
    """Calcule des indicateurs agregés pour le QAQC."""
    records = []
    n = len(df)

    def pct(mask):
        return round(100 * mask.sum() / n, 2) if n > 0 else 0

    # Population
    records.append({"indicateur": "Total individus", "valeur": n, "unite": "personnes"})

    # Sexe
    if "sexe" in df.columns:
        for val in ["Masculin", "Feminin"]:
            records.append({
                "indicateur": f"Proportion {val}",
                "valeur": pct(df["sexe"] == val),
                "unite": "%",
            })

    # Milieu
    if "milieu" in df.columns:
        for val in ["Urbain", "Rural"]:
            records.append({
                "indicateur": f"Proportion {val}",
                "valeur": pct(df["milieu"] == val),
                "unite": "%",
            })

    # Age median
    if "age" in df.columns:
        records.append({
            "indicateur": "Age median",
            "valeur": round(df["age"].median(), 1),
            "unite": "annees",
        })

    # Taux de scolarisation (6-15 ans)
    if "age" in df.columns and "scolarise" in df.columns:
        enfants_6_15 = df["age"].between(6, 15)
        if enfants_6_15.sum() > 0:
            scol = (df.loc[enfants_6_15, "scolarise"] == "Actuellement scolarise").sum()
            records.append({
                "indicateur": "Taux de scolarisation 6-15 ans",
                "valeur": round(100 * scol / enfants_6_15.sum(), 2),
                "unite": "%",
            })

    # Taux d'alphabetisation (15 ans et +)
    if "age" in df.columns and "alphabetise" in df.columns:
        pop_15plus = df["age"] >= 15
        if pop_15plus.sum() > 0:
            alpha = df.loc[pop_15plus, "alphabetise"].sum()
            records.append({
                "indicateur": "Taux d'alphabetisation (15 ans et +)",
                "valeur": round(100 * alpha / pop_15plus.sum(), 2),
                "unite": "%",
            })
        # Par sexe
        for sexe in ["Masculin", "Feminin"]:
            if "sexe" in df.columns:
                mask_s = pop_15plus & (df["sexe"] == sexe)
                if mask_s.sum() > 0:
                    a = df.loc[mask_s, "alphabetise"].sum()
                    records.append({
                        "indicateur": f"Taux alpha (15+) - {sexe}",
                        "valeur": round(100 * a / mask_s.sum(), 2),
                        "unite": "%",
                    })

    # Alphabetisation par langue
    for col in config.ALPHA_COLS_NORM:
        if col in df.columns:
            pop_15plus = df.get("age", pd.Series(dtype=float)) >= 15
            if pop_15plus.sum() > 0:
                a = df.loc[pop_15plus, col].fillna(0).sum()
                langue = col.replace("alpha_", "")
                records.append({
                    "indicateur": f"Taux alpha {langue} (15+)",
                    "valeur": round(100 * a / pop_15plus.sum(), 2),
                    "unite": "%",
                })

    # Distribution par region
    if "region" in df.columns:
        for reg, cnt in df["region"].value_counts().head(14).items():
            records.append({
                "indicateur": f"Effectif region {reg}",
                "valeur": int(cnt),
                "unite": "personnes",
            })

    return pd.DataFrame(records)


# ==============================================================================
# PROGRAMME PRINCIPAL
# ==============================================================================
def main():
    print("=" * 60)
    print("PIPELINE INDIVIDUS - Nettoyage et derivation")
    print("Module : Demographiques, Geographiques, Education")
    print("Source : 10eme RGPH Senegal - Section B")
    print("=" * 60)

    # A. Chargement
    df, n_raw = load_selected()

    # B. Manquants
    df = traiter_manquants(df)
    df_miss = missing_summary(df)

    # C. Aberrants
    df = traiter_aberrants(df)
    df_outl = outlier_summary(df)

    # D. Recodage
    df = recoder(df)

    # E. Derivation
    df = deriver_variables(df)

    # F. Coherence
    df = controler_coherence(df)
    df_coher = run_coherence_checks(df, config.COHERENCE_CHECKS)

    # G. Distributions
    df_distrib = compute_all_distributions(df, config.CAT_VARS_QAQC)

    # H. Estimations
    df_estim = calcul_estimations(df)

    # I. Nettoyage final : suppression des colonnes de flags
    cols_flags = [c for c in df.columns if c.endswith("_flag_miss") or c.endswith("_flag_outlier")]
    df_clean = df.drop(columns=cols_flags)

    # J. Export CSV
    config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    df_clean.to_csv(config.IND_CLEAN_CSV, index=False, encoding="utf-8-sig")
    print(f"\n>> Table individus exportee : {config.IND_CLEAN_CSV}")
    print(f"   Dimensions finales : {df_clean.shape[0]:,} x {df_clean.shape[1]} colonnes")

    # K. QAQC
    generate_qaqc(
        df_clean=df_clean,
        df_missing=df_miss,
        df_outliers=df_outl,
        df_distributions=df_distrib,
        df_coherence=df_coher,
        df_estimations=df_estim,
        output_path=config.QAQC_XLSX,
        n_raw=n_raw,
    )

    print("\n>> Pipeline individus TERMINE avec succes.")
    print(f"   - Table nettoyee  : {config.IND_CLEAN_CSV}")
    print(f"   - Rapport QAQC    : {config.QAQC_XLSX}")
    print("=" * 60)


if __name__ == "__main__":
    main()
