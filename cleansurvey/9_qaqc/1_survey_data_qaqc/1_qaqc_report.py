import sys
import os
import pandas as pd
import numpy as np

# Configurer le chemin racine
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from cleansurvey.config import OUTPUT_DIR, QAQC_DIR

def calculate_qaqc():
    print("--- DEBUT DU CALCUL DES INDICATEURS QAQC ---")
    merged_file = os.path.join(OUTPUT_DIR, "rgph5_merged.csv")
    
    if not os.path.exists(merged_file):
        # Repli sur le fichier individuel propre si pas de fusion
        merged_file = os.path.join(OUTPUT_DIR, "rgph5_ind_clean.csv")
        
    if not os.path.exists(merged_file):
        print(f"Erreur : Aucun fichier de données propres trouvé.")
        sys.exit(1)
        
    df = pd.read_csv(merged_file)
    total_obs = len(df)
    
    # Initialiser le rapport Markdown
    report = []
    report.append("# Rapport d'Assurance Qualité (QAQC) - Recensement RGPH-5 (Groupe 2 - Individus)")
    report.append(f"Ce rapport contient les estimations descriptives primaires après traitement des données d'individus.")
    report.append(f"**Nombre total d'observations traitées** : {total_obs:,} individus.\n")
    report.append("---")
    
    # 1. ANALYSE DES VALEURS MANQUANTES
    report.append("## 1. Analyse des valeurs manquantes (Taux de vide)")
    missing_pct = (df.isna().mean() * 100).round(2)
    missing_df = pd.DataFrame({
        "Variable": missing_pct.index,
        "Taux de valeurs manquantes (%)": missing_pct.values
    }).sort_values(by="Taux de valeurs manquantes (%)", ascending=False)
    
    report.append(missing_df.to_markdown(index=False))
    report.append("\n")
    
    # 2. CARACTÉRISTIQUES DÉMOGRAPHIQUES
    report.append("## 2. Caractéristiques Démographiques")
    
    # Sexe
    report.append("### Répartition par Sexe (Genre)")
    if 'sexe' in df.columns:
        sexe_counts = df['sexe'].value_counts(dropna=False)
        sexe_pct = df['sexe'].value_counts(normalize=True, dropna=False) * 100
        sexe_df = pd.DataFrame({
            "Sexe": sexe_counts.index,
            "Effectif": sexe_counts.values,
            "Pourcentage (%)": sexe_pct.values.round(2)
        })
        report.append(sexe_df.to_markdown(index=False))
        
        # Calcul du Sex-Ratio (Hommes / Femmes)
        males = (df['sexe'] == 'Masculin').sum()
        females = (df['sexe'] == 'Féminin').sum()
        if females > 0:
            sex_ratio = (males / females) * 100
            report.append(f"\n* **Sex-ratio** : {sex_ratio:.2f} hommes pour 100 femmes.\n")
    else:
        report.append("Variable 'sexe' non disponible.")
    
    # Âge
    report.append("### Structure par Âge")
    if 'age' in df.columns:
        mean_age = df['age'].mean()
        median_age = df['age'].median()
        
        # Tranches d'âge
        bins = [0, 5, 12, 15, 18, 25, 65, 120]
        labels = ['0-4 ans', '5-11 ans', '12-14 ans', '15-17 ans', '18-24 ans', '25-64 ans', '65 ans et +']
        df['age_group'] = pd.cut(df['age'], bins=bins, labels=labels, right=False)
        age_group_counts = df['age_group'].value_counts(dropna=False)
        age_group_pct = df['age_group'].value_counts(normalize=True, dropna=False) * 100
        
        age_group_df = pd.DataFrame({
            "Tranche d'âge": age_group_counts.index,
            "Effectif": age_group_counts.values,
            "Pourcentage (%)": age_group_pct.values.round(2)
        })
        
        report.append(f"- **Âge moyen** : {mean_age:.1f} ans")
        report.append(f"- **Âge médian** : {median_age:.1f} ans\n")
        report.append(age_group_df.to_markdown(index=False))
        report.append("\n")
    else:
        report.append("Variable 'age' non disponible.")
        
    # Situation matrimoniale
    report.append("### Situation Matrimoniale (15 ans et +)")
    if 'situation_matrimoniale' in df.columns:
        df_15 = df[df['age'] >= 15]
        mat_counts = df_15['situation_matrimoniale'].value_counts(dropna=False)
        mat_pct = df_15['situation_matrimoniale'].value_counts(normalize=True, dropna=False) * 100
        mat_df = pd.DataFrame({
            "Situation matrimoniale": mat_counts.index,
            "Effectif": mat_counts.values,
            "Pourcentage (%)": mat_pct.values.round(2)
        })
        report.append(mat_df.to_markdown(index=False))
        report.append("\n")
        
    # Lien de parenté avec le CM
    report.append("### Lien de Parenté avec le CM")
    if 'lien_parente' in df.columns:
        lp_counts = df['lien_parente'].value_counts(dropna=False)
        lp_pct = df['lien_parente'].value_counts(normalize=True, dropna=False) * 100
        lp_df = pd.DataFrame({
            "Lien de parenté": lp_counts.index,
            "Effectif": lp_counts.values,
            "Pourcentage (%)": lp_pct.values.round(2)
        })
        report.append(lp_df.to_markdown(index=False))
        report.append("\n")
        
    # Niveau d'études
    report.append("### Niveau d'Études")
    if 'niveau_etudes' in df.columns:
        ne_counts = df['niveau_etudes'].value_counts(dropna=False)
        ne_pct = df['niveau_etudes'].value_counts(normalize=True, dropna=False) * 100
        ne_df = pd.DataFrame({
            "Niveau d'études": ne_counts.index,
            "Effectif": ne_counts.values,
            "Pourcentage (%)": ne_pct.values.round(2)
        })
        report.append(ne_df.to_markdown(index=False))
        report.append("\n")

    # 3. CARACTÉRISTIQUES GÉOGRAPHIQUES
    report.append("## 3. Répartition Géographique")
    
    # Région
    report.append("### Répartition par Région")
    if 'region' in df.columns:
        reg_counts = df['region'].value_counts(dropna=False)
        reg_pct = df['region'].value_counts(normalize=True, dropna=False) * 100
        reg_df = pd.DataFrame({
            "Région": reg_counts.index,
            "Effectif": reg_counts.values,
            "Pourcentage (%)": reg_pct.values.round(2)
        })
        report.append(reg_df.to_markdown(index=False))
        report.append("\n")
        
    # Milieu de résidence
    report.append("### Répartition par Milieu de Résidence")
    if 'milieu_residence' in df.columns:
        mil_counts = df['milieu_residence'].value_counts(dropna=False)
        mil_pct = df['milieu_residence'].value_counts(normalize=True, dropna=False) * 100
        mil_df = pd.DataFrame({
            "Milieu de résidence": mil_counts.index,
            "Effectif": mil_counts.values,
            "Pourcentage (%)": mil_pct.values.round(2)
        })
        report.append(mil_df.to_markdown(index=False))
        report.append("\n")
        
    # 4. CARACTÉRISTIQUES ÉDUCATIVES
    report.append("## 4. Caractéristiques Éducatives")
    
    # Scolarisation
    report.append("### Scolarisation")
    if 'scolarisation' in df.columns:
        # Taux de scolarisation par tranches d'âge scolaires
        # Primaire (6-11 ans) et Moyen/Secondaire (12-18 ans)
        df_prim = df[df['age'].between(6, 11)]
        df_sec = df[df['age'].between(12, 18)]
        
        report.append("#### Taux de scolarisation chez les enfants de 6-11 ans (âge du primaire)")
        if len(df_prim) > 0:
            scol_prim_pct = (df_prim['scolarisation'] == 'oui, fréquente actuellement').mean() * 100
            report.append(f"* **Taux d'inscription scolaire active (6-11 ans)** : {scol_prim_pct:.2f}%\n")
        else:
            report.append("* Aucun individu âgé de 6-11 ans trouvé.\n")
            
        report.append("#### Taux de scolarisation chez les adolescents de 12-18 ans (âge du moyen/secondaire)")
        if len(df_sec) > 0:
            scol_sec_pct = (df_sec['scolarisation'] == 'oui, fréquente actuellement').mean() * 100
            report.append(f"* **Taux d'inscription scolaire active (12-18 ans)** : {scol_sec_pct:.2f}%\n")
        else:
            report.append("* Aucun individu âgé de 12-18 ans trouvé.\n")
            
    # Alphabétisation
    report.append("### Alphabétisation par langue (Population de 5 ans et plus)")
    df_5 = df[df['age'] >= 5]
    if len(df_5) > 0:
        alpha_cols = [c for c in df.columns if c.startswith('alpha_')]
        alpha_rates = []
        for col in alpha_cols:
            lang_name = col.replace('alpha_', '').upper()
            # Si modalité 'Oui' ou '1' ou nom de la langue
            # Dans notre modalité initial c'est souvent 'Oui' ou 'Wolof' etc.
            # Tout ce qui est différent de 'Non' et non nul est Oui
            total_valid = df_5[col].dropna()
            if len(total_valid) > 0:
                is_yes = total_valid.astype(str).str.lower().str.strip().isin(['oui', '1', '1.0']) | \
                         (~total_valid.astype(str).str.lower().str.strip().isin(['non', '0', '0.0', 'nan', 'none']))
                rate = is_yes.mean() * 100
                alpha_rates.append({
                    "Langue": lang_name,
                    "Taux d'alphabétisation (%)": round(rate, 2)
                })
        if alpha_rates:
            alpha_df = pd.DataFrame(alpha_rates).sort_values(by="Taux d'alphabétisation (%)", ascending=False)
            report.append(alpha_df.to_markdown(index=False))
            report.append("\n")
        else:
            report.append("Aucune variable d'alphabétisation disponible ou documentée.")
    else:
        report.append("Aucun individu de 5 ans et plus pour estimer l'alphabétisation.")
        
    # 5. CARACTÉRISTIQUES DE L'EMPLOI
    report.append("## 5. Caractéristiques de l'Emploi (Population de 15 ans et +)")
    df_15 = df[df['age'] >= 15]
    if len(df_15) > 0:
        # Statut d'emploi
        if 'statut_emploi' in df.columns:
            report.append("### Répartition par Statut d'Emploi")
            counts = df_15['statut_emploi'].value_counts(dropna=False)
            pct = df_15['statut_emploi'].value_counts(normalize=True, dropna=False) * 100
            df_se = pd.DataFrame({"Statut": counts.index, "Effectif": counts.values, "Pourcentage (%)": pct.values.round(2)})
            report.append(df_se.to_markdown(index=False))
            report.append("\n")
            
        # Secteur institutionnel
        if 'secteur_instit' in df.columns:
            report.append("### Répartition par Secteur d'Activité (Secteur Institutionnel)")
            counts = df_15['secteur_instit'].value_counts(dropna=False)
            pct = df_15['secteur_instit'].value_counts(normalize=True, dropna=False) * 100
            df_si = pd.DataFrame({"Secteur": counts.index, "Effectif": counts.values, "Pourcentage (%)": pct.values.round(2)})
            report.append(df_si.to_markdown(index=False))
            report.append("\n")
            
        # Profession (Top 10)
        if 'profession' in df.columns:
            report.append("### Top 10 des Professions les plus représentées")
            counts = df_15['profession'].value_counts(dropna=True).head(10)
            pct = df_15['profession'].value_counts(normalize=True, dropna=True).head(10) * 100
            df_prof = pd.DataFrame({"Profession": counts.index, "Effectif": counts.values, "Pourcentage (%)": pct.values.round(2)})
            report.append(df_prof.to_markdown(index=False))
            report.append("\n")
            
        # Revenu d'emploi estimé moyen
        if 'revenu_emploi_estime' in df.columns:
            report.append("### Estimation du Revenu d'Emploi Moyen (FCFA)")
            if 'secteur_instit' in df.columns:
                # Filtrer les occupés uniquement pour le calcul
                df_occ = df_15[df_15['statut_emploi'].isin(['Occupé', '1', '1.0'])]
                if len(df_occ) > 0:
                    rev_secteur = df_occ.groupby('secteur_instit')['revenu_emploi_estime'].mean().round(0).reset_index()
                    rev_secteur.columns = ["Secteur Institutionnel", "Revenu Moyen Estimé (FCFA)"]
                    report.append(rev_secteur.to_markdown(index=False))
                    report.append("\n")
                else:
                    report.append("Aucun individu occupé trouvé pour estimer le revenu par secteur.\n")
            else:
                mean_rev = df_15['revenu_emploi_estime'].mean()
                report.append(f"* **Revenu moyen global (15 ans et +)** : {mean_rev:,.0f} FCFA\n")
    else:
        report.append("Aucune observation de 15 ans et plus pour analyser l'emploi.\n")

    # 6. ANALYSE DU HANDICAP (Washington Group)
    report.append("## 6. Analyse du Handicap (Washington Group)")
    handicap_cols = ['handicap_vision', 'handicap_audition', 'handicap_moteur', 'handicap_cognitif', 'handicap_soins', 'handicap_communication']
    handicap_rates = []
    for col in handicap_cols:
        if col in df.columns:
            rate = (df[col] == 1).mean() * 100
            handicap_rates.append({
                "Type de Limitation (Handicap)": col.replace('handicap_', '').capitalize(),
                "Taux de prévalence (%)": round(rate, 2)
            })
    if handicap_rates:
        df_h = pd.DataFrame(handicap_rates).sort_values(by="Taux de prévalence (%)", ascending=False)
        report.append(df_h.to_markdown(index=False))
        report.append("\n")
        
        avail_cols = [c for c in handicap_cols if c in df.columns]
        if avail_cols:
            df['any_handicap'] = (df[avail_cols] == 1).any(axis=1).astype(int)
            global_prev = df['any_handicap'].mean() * 100
            report.append(f"* **Taux de prévalence globale (au moins une limitation sévère)** : {global_prev:.2f}%\n")
    else:
        report.append("Aucune variable de handicap disponible.\n")

    # 7. ANALYSE DE LA MIGRATION
    report.append("## 7. Analyse de la Migration et Résidence")
    if 'situation_residence' in df.columns:
        report.append("### Répartition de la population par Situation de Résidence")
        counts = df['situation_residence'].value_counts(dropna=False)
        pct = df['situation_residence'].value_counts(normalize=True, dropna=False) * 100
        df_sr = pd.DataFrame({"Situation de résidence": counts.index, "Effectif": counts.values, "Pourcentage (%)": pct.values.round(2)})
        report.append(df_sr.to_markdown(index=False))
        report.append("\n")
        
    if 'region_residence_1an' in df.columns and 'region' in df.columns:
        report.append("### Taux de migration interne inter-régionale depuis 1 an")
        df_mig = df[df['region_residence_1an'].notna() & (df['region_residence_1an'] != df['region'])]
        mig_rate = (len(df_mig) / len(df)) * 100
        report.append(f"* **Taux de migration interne récente (inter-régionale)** : {mig_rate:.2f}% de la population a changé de région de résidence au cours de l'année passée.\n")
        
        if len(df_mig) > 0:
            report.append("#### Top 5 des régions de destination des migrants récents")
            dest = df_mig['region'].value_counts().head(5).reset_index()
            dest.columns = ["Région de destination", "Nombre de migrants"]
            report.append(dest.to_markdown(index=False))
            report.append("\n")

    # Sauvegarder le rapport
    out_path = os.path.join(QAQC_DIR, "qaqc_report.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report))
        
    print(f"✔ Rapport QAQC sauvegardé dans : {out_path}")

if __name__ == "__main__":
    calculate_qaqc()
