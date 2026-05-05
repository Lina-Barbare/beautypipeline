# BeautyPipeline

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)
![DuckDB](https://img.shields.io/badge/DuckDB-Warehouse-FFC300?style=flat-square)
![SQL](https://img.shields.io/badge/SQL-Transformations-336791?style=flat-square)
![Rich](https://img.shields.io/badge/Rich-CLI-green?style=flat-square)

---

## C'est quoi ce projet

J'ai construit un pipeline de donnees complet sur un dataset de produits cosmetiques Sephora (1 472 produits, 116 marques, 6 categories).

L'idee c'etait pas juste d'analyser des donnees comme je l'aurais fait en data science — c'etait de construire un vrai systeme qui ingere, nettoie, structure et stocke la donnee de facon fiable et reproductible. A chaque execution, le pipeline repart de zero, recharge tout, et verifie automatiquement que les donnees sont propres.

---

## Ce que fait le pipeline

```
cosmetics.csv
     |
     v
[1] Extraction      ->  chargement + validation du schema + profil des donnees
     |
     v
[2] Transformation  ->  nettoyage, feature engineering, structuration en tables
     |
     v
[3] Chargement      ->  insertion dans DuckDB (3 schemas : staging / dimensions / mart)
     |
     v
[4] Modeles SQL     ->  vues analytiques style DBT
     |
     v
[5] Tests qualite   ->  10 tests automatiques sur l'integrite des donnees
```

---

## Pourquoi ces choix techniques

**DuckDB** plutot que SQLite ou PostgreSQL : DuckDB est fait pour l'analytique, il supporte les fenetres SQL (RANK, ROW_NUMBER, QUALIFY), il est tres rapide sur des requetes agregees, et sa syntaxe est identique a celle de Snowflake. C'est ce qui m'a motivee a l'utiliser plutot qu'une simple base relationnelle classique.

**3 couches de donnees** (staging / dimensions / mart) : j'ai suivi la logique d'un vrai data warehouse. Le staging contient les donnees brutes nettoyees, les dimensions centralisent les referentiels (marques, categories), et le mart contient les tables prets a l'emploi pour l'analyse. Ca rend les requetes plus lisibles et ca facilite la maintenance.

**Les tests qualite** : c'est la partie que j'ai trouvee la plus utile a comprendre. En data engineering on ne peut pas se contenter de "ca a l'air bon". Il faut des regles explicites : est-ce qu'il y a des valeurs nulles ? Les prix sont-ils positifs ? Les segments de prix sont-ils coherents avec les valeurs attendues ? J'ai code 10 tests qui s'executent a chaque lancement du pipeline.

**Rich** pour l'affichage : j'ai ajoute cette librairie pour remplacer les print() basiques par un affichage structure avec des tableaux, des couleurs et une barre de progression. Ca rend le pipeline plus lisible quand on le fait tourner.

---

## Structure

```
beautypipeline/
├── data/
│   ├── cosmetics.csv               <- dataset Kaggle
│   └── beauty_warehouse.duckdb     <- base generee automatiquement
├── pipeline/
│   ├── extract.py                  <- chargement et validation
│   ├── transform.py                <- nettoyage et enrichissement
│   └── load.py                     <- insertion dans DuckDB
├── models/
│   └── transformations.sql         <- vues analytiques (style DBT)
├── tests/
│   └── quality_checks.py           <- tests d'integrite des donnees
├── main.py                         <- orchestration du pipeline
├── requirements.txt
└── README.md
```

---

## Comment lancer le projet

**1. Telecharger le dataset**
Kaggle : [Cosmetics datasets par Abid Ali Awan](https://www.kaggle.com/datasets/abidaliawan/cosmetics-datasets)
Placer le CSV dans `data/` et le renommer `cosmetics.csv`.

**2. Installer les dependances**
```bash
pip install -r requirements.txt
```

**3. Lancer**
```bash
python main.py
```

Le pipeline s'execute en moins d'une seconde et affiche un bilan complet.

---

## Ce que j'aurais fait avec plus de temps

- Ajouter un vrai orchestrateur (Prefect ou Airflow) pour executer le pipeline en mode planifie
- Connecter a un vrai Snowflake pour tester en environnement cloud
- Ajouter des transformations DBT reelles plutot que des vues SQL manuelles
- Construire un dashboard de monitoring sur la qualite des donnees

---

## A propos

Barbare Lina — Etudiante Master 1 Data Science — 2025
