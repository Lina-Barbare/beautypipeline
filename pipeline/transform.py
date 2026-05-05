"""
BeautyPipeline - Etape 2 : Transformation
==========================================
Nettoyage, enrichissement et structuration
des donnees avant chargement en base.
"""

import pandas as pd
import numpy as np
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [TRANSFORM] %(message)s")
log = logging.getLogger(__name__)


def nettoyer_donnees(df: pd.DataFrame) -> pd.DataFrame:
    """
    Nettoyage de base :
    - suppression des doublons
    - suppression des lignes sans nom ou marque
    - normalisation des textes
    - nettoyage des prix
    """
    nb_initial = len(df)
    df = df.copy()

    # Suppression des doublons
    df = df.drop_duplicates()
    log.info(f"Doublons supprimes : {nb_initial - len(df)}")

    # Suppression des lignes sans nom ou marque (donnees critiques)
    df = df.dropna(subset=["Name", "Brand"])
    log.info(f"Lignes sans nom/marque supprimees : {nb_initial - len(df)}")

    # Normalisation des textes : suppression des espaces superflus
    for col in ["Name", "Brand", "Label"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    # Nettoyage de la colonne prix : on garde uniquement les valeurs numeriques positives
    if "Price" in df.columns:
        df["Price"] = pd.to_numeric(df["Price"], errors="coerce")
        df = df[df["Price"] > 0]
        log.info(f"Lignes avec prix invalide supprimees. Reste : {len(df):,}")

    # Nettoyage du score (Rank) : entre 0 et 5
    if "Rank" in df.columns:
        df["Rank"] = pd.to_numeric(df["Rank"], errors="coerce")
        df = df[df["Rank"].between(0, 5)]

    log.info(f"Nettoyage termine : {len(df):,} lignes valides")
    return df


def enrichir_donnees(df: pd.DataFrame) -> pd.DataFrame:
    """
    Feature engineering :
    - segment de prix
    - comptage des ingredients
    - score de popularite normalise
    - flag produit premium
    """
    df = df.copy()

    # Segment de prix : budget / milieu de gamme / premium / luxe
    def segmenter_prix(prix):
        if pd.isna(prix):
            return "inconnu"
        if prix < 15:
            return "budget"
        elif prix < 40:
            return "milieu_de_gamme"
        elif prix < 80:
            return "premium"
        else:
            return "luxe"

    df["segment_prix"] = df["Price"].apply(segmenter_prix)

    # Nombre d'ingredients (si la colonne existe)
    if "Ingredients" in df.columns:
        df["nb_ingredients"] = df["Ingredients"].astype(str).apply(
            lambda x: len(x.split(",")) if x != "nan" else 0
        )
        log.info(f"Nombre moyen d'ingredients : {df['nb_ingredients'].mean():.1f}")

    # Score de popularite normalise entre 0 et 1
    if "Rank" in df.columns:
        df["score_popularite"] = df["Rank"] / 5.0

    # Flag produit premium (prix > 60)
    if "Price" in df.columns:
        df["est_premium"] = (df["Price"] > 60).astype(int)

    # Types de peau (colonnes binaires si presentes dans le dataset)
    types_peau = ["Combination", "Dry", "Normal", "Oily", "Sensitive"]
    cols_peau = [c for c in types_peau if c in df.columns]
    if cols_peau:
        df["nb_types_peau_compatibles"] = df[cols_peau].sum(axis=1)
        log.info(f"Colonnes types de peau trouvees : {cols_peau}")

    log.info("Enrichissement termine")
    return df


def structurer_en_tables(df: pd.DataFrame) -> dict:
    """
    Separation des donnees en tables distinctes
    comme dans un vrai entrepot de donnees (Data Warehouse).

    Retourne un dictionnaire avec :
    - stg_produits : table de staging complete
    - dim_marques : table de dimension des marques
    - dim_categories : table de dimension des categories
    - fait_produits : table de faits pour l'analyse
    """
    tables = {}

    # Table de staging : toutes les donnees nettoyees
    tables["stg_produits"] = df.copy()

    # Dimension marques : une ligne par marque avec agregats
    if "Brand" in df.columns:
        dim_marques = df.groupby("Brand").agg(
            nb_produits=("Name", "count"),
            prix_moyen=("Price", "mean"),
            score_moyen=("Rank", "mean"),
        ).round(2).reset_index()
        dim_marques.columns = ["marque", "nb_produits", "prix_moyen", "score_moyen"]
        dim_marques["marque_id"] = range(1, len(dim_marques) + 1)
        tables["dim_marques"] = dim_marques
        log.info(f"Dimension marques : {len(dim_marques)} marques distinctes")

    # Dimension categories (Label)
    if "Label" in df.columns:
        dim_categories = df[["Label"]].drop_duplicates().reset_index(drop=True)
        dim_categories.columns = ["categorie"]
        dim_categories["categorie_id"] = range(1, len(dim_categories) + 1)
        tables["dim_categories"] = dim_categories
        log.info(f"Dimension categories : {len(dim_categories)} categories distinctes")

    # Table de faits : une ligne par produit avec toutes les mesures
    cols_faits = ["Name", "Brand", "Label", "Price", "Rank",
                  "segment_prix", "score_popularite", "est_premium"]
    if "nb_ingredients" in df.columns:
        cols_faits.append("nb_ingredients")
    if "nb_types_peau_compatibles" in df.columns:
        cols_faits.append("nb_types_peau_compatibles")

    cols_existantes = [c for c in cols_faits if c in df.columns]
    tables["fait_produits"] = df[cols_existantes].copy()
    log.info(f"Table de faits : {len(tables['fait_produits']):,} produits")

    return tables


def transformer(df_brut: pd.DataFrame) -> dict:
    """Fonction principale de transformation."""
    log.info("Debut de la transformation...")

    df = nettoyer_donnees(df_brut)
    df = enrichir_donnees(df)
    tables = structurer_en_tables(df)

    log.info(f"Transformation terminee. Tables produites : {list(tables.keys())}")
    return tables


if __name__ == "__main__":
    df_test = pd.read_csv("data/cosmetics.csv")
    tables = transformer(df_test)
    for nom, table in tables.items():
        print(f"\n{nom} : {table.shape}")
        print(table.head(2))
