# BeautyPipeline - Pipeline de donnees cosmetiques

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)
![DuckDB](https://img.shields.io/badge/DuckDB-Data%20Warehouse-FFC300?style=flat-square)
![SQL](https://img.shields.io/badge/SQL-Transformations-336791?style=flat-square)

---

## Presentation

Ce projet est mon premier projet de Data Engineering.
J'ai voulu construire un pipeline complet de bout en bout, depuis la donnee brute jusqu'a un entrepot de donnees interrogeable en SQL.

Le dataset utilise contient environ 9000 produits cosmetiques avec leurs ingredients, marques, prix et notes (source Kaggle).
J'ai choisi ce domaine parce que ca me semblait concret et representatif de problematiques reelles dans une entreprise de grande consommation.

---

## Ce que fait le pipeline

```
CSV brut  ->  Extraction  ->  Transformation  ->  DuckDB  ->  Modeles SQL  ->  Tests qualite
```

1. **Extraction** : chargement du CSV, validation du schema, profil des donnees
2. **Transformation** : nettoyage, feature engineering, structuration en tables (staging / dimensions / faits)
3. **Chargement** : insertion dans DuckDB, organise en 3 schemas (staging, dimensions, mart)
4. **Modeles SQL** : vues analytiques qui transforment les donnees pour l'analyse (style DBT)
5. **Tests qualite** : verification automatique de l'integrite des donnees (not_null, plages de valeurs, coherence metier)

---

## Structure du projet

```
beautypipeline/
├── data/
│   ├── cosmetics.csv           <- dataset Kaggle (a telecharger)
│   └── beauty_warehouse.duckdb <- base generee automatiquement
├── pipeline/
│   ├── extract.py              <- chargement et validation
│   ├── transform.py            <- nettoyage et enrichissement
│   └── load.py                 <- insertion dans DuckDB
├── models/
│   └── transformations.sql     <- modeles SQL analytiques (style DBT)
├── tests/
│   └── quality_checks.py       <- tests de qualite automatiques
├── main.py                     <- orchestration du pipeline complet
├── requirements.txt
└── README.md
```

---

## Outils utilises et pourquoi

| Outil | Role | Equivalent en entreprise |
|---|---|---|
| Python + Pandas | Extraction et transformation | Base du pipeline |
| DuckDB | Data warehouse local | Snowflake / BigQuery |
| SQL (vues) | Transformations analytiques | DBT |
| Tests Python | Controle qualite | Tests DBT / Great Expectations |

J'ai choisi DuckDB parce que c'est gratuit, leger, et utilise exactement la meme syntaxe SQL que Snowflake. L'idee etait d'apprendre la logique d'un data warehouse sans avoir besoin d'un compte cloud.

---

## Comment lancer le projet

**1. Telecharger le dataset**
Sur Kaggle : [Cosmetics and Skincare Products](https://www.kaggle.com/datasets/kingabzpro/cosmetics-ingredients-dataset)
Placer le fichier CSV dans le dossier `data/` et le renommer `cosmetics.csv`.

**2. Installer les dependances**
```bash
pip install -r requirements.txt
```

**3. Lancer le pipeline**
```bash
python main.py
```

Le pipeline s'execute en entier et affiche un bilan a la fin.

**4. Interroger la base directement en SQL**
```python
import duckdb
conn = duckdb.connect("data/beauty_warehouse.duckdb")

# Exemple : top 10 marques par score
conn.execute("""
    SELECT marque, nb_produits, prix_moyen, score_moyen
    FROM mart.analyse_marques
    LIMIT 10
""").fetchdf()
```

---

## Exemples de resultats

Le pipeline produit plusieurs vues analytiques directement interrogeables :

- `mart.analyse_marques` : positionnement de chaque marque (prix, score, catalogue)
- `mart.analyse_categories` : comparaison des categories (Moisturizer, Serum, Cleanser...)
- `mart.top_produits_par_categorie` : top 5 produits par categorie
- `mart.matrice_prix_score` : identification des "bonnes affaires" vs produits surpay?s

---

## Ce que j'ai appris

C'est le projet ou j'ai le plus progresse techniquement.
Structurer les donnees en couches (staging, dimensions, mart), ecrire des tests de qualite automatiques, penser en termes de pipeline plutot que de script isole : tout ca m'a ouvert sur la logique du Data Engineering.

La partie que j'ai trouvee la plus difficile c'est la conception du schema en tables separees. Au debut je voulais tout mettre dans une seule table, et j'ai compris progressivement pourquoi la separation dimensions / faits est importante pour la performance et la lisibilite des requetes.

---

## A propos

Barbare Lina - Etudiante Master 1 Data Science - 2025
