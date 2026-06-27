# Groupe 2 — Pipeline de traitement RGPH-5

## Description

Pipeline de traitement des données du 5ème Recensement Général de la Population et de l'Habitat du Sénégal (RGPH-5). Ce dépôt contient la partie **ménage** du pipeline développé par le Groupe 2.

## Structure du projet

```
cleansurvey/
├── config.py                          # Configuration centrale (chemins, seuils, paramètres)
├── utils.py                           # Fonctions utilitaires partagées
├── run_all.py                         # Point d'entrée — lance tout le pipeline
│
├── 1_data_exploration/
│   ├── 1_get_initial_dict/
│   │   └── 1_get_hh_dict.py          # Étape 1 — Dictionnaire des variables
│   └── 2_select_and_label/
│       └── 1_apply_hh_dict.py        # Étape 2 — Sélection et étiquetage
│
└── 2_clean_and_merge/
    ├── 1_clean_hh_ind.py              # Étape 3 — Nettoyage et imputation
    ├── 2_merge_hh_ind.py             # Étape 4 — Fusion table finale
    └── 3_qaqc_menage.py              # Étape 5 — Rapport QAQC
```

## Données requises

Placer les fichiers `.sav` dans le dossier `data/` :

```
data/
├── indiv_SECTION_B.sav
└── habitat_SECTION_E.sav
```

## Installation

```bash
pip install -r requirements.txt
```

## Utilisation

```bash
cd cleansurvey
python run_all.py
```

## Outputs produits

| Fichier | Description |
|---|---|
| `output/dict/hh_dict.xlsx` | Dictionnaire des 388 variables disponibles |
| `output/labeled/hh_labeled.csv` | Table ménage avec labels texte (60 771 lignes) |
| `output/clean/hh_clean.csv` | Table ménage propre après nettoyage et imputation |
| `output/clean/hh_qaqc_log.csv` | Log des 12 contrôles qualité effectués |
| `output/final/hh_final.csv` | Table ménage finale (15 variables) |
| `output/qaqc/qaqc_menage.xlsx` | Rapport QAQC Excel (9 onglets) |
| `output/qaqc/qaqc_menage.html` | Rapport QAQC HTML |

## Variables de la table finale

| Variable | Description | Source |
|---|---|---|
| `A06` + `A09` | Clé unique du ménage (district + numéro) | Sections B & E |
| `region` | Région de résidence | Section E — A01 |
| `departement` | Département | Section E — A02 |
| `commune` | Commune | Section E — A04 |
| `milieu` | Milieu de résidence (Urbain/Rural) | Section E — A10 |
| `type_menage` | Type de ménage (Ordinaire/Collectif) | Section E — A11 |
| `taille_menage` | Taille du ménage (nb de membres) | Calculée depuis Section B |
| `age_cm` | Âge du chef de ménage | Section B — AGE_CM |
| `sexe_cm` | Sexe du chef de ménage | Section B — B06 |
| `niveau_etude_cm` | Niveau d'études du CM | Section B — B33 |
| `situation_matrimoniale_cm` | Situation matrimoniale du CM | Section B — B41 |
| `statut_emploi_cm` | Statut d'emploi du CM | Section B — B36 |
| `branche_isic_cm` | Branche d'activité ISIC Rev 4 | Section B — B39A |
| `secteur_instit_cm` | Secteur institutionnel | Section B — B39B |

## Décisions méthodologiques clés

**Clé ménage** — `A09` seul insuffisant (78 valeurs uniques). Clé composite `A06 + A09` utilisée → 60 411 ménages uniques.

**Valeurs aberrantes** — Âge CM : bornes [0, 120]. Taille ménage : seuil au 99e percentile = 125 membres.

**Imputation** — Test de skewness avant imputation : `taille_menage` (skewness=1.256) → médiane=12 ; `age_cm` (skewness=0.406) → moyenne=46.49. Variables qualitatives → mode.

**Sauts de questionnaire** — `niveau_etude_cm` : CM non scolarisés → "Non scolarisé". `branche_isic_cm` et `secteur_instit_cm` : CM inactifs → "Sans activité".

## Compatibilité

Le pipeline est conçu pour être réutilisable pour un futur recensement. Tous les paramètres modifiables (chemins, seuils, codes manquants, identifiants) sont centralisés dans `config.py`.
