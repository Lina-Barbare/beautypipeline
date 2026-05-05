"""
BeautyPipeline - Etape 3 : Chargement
=======================================
Chargement des tables transformees dans DuckDB.
DuckDB est utilise ici comme equivalent local de Snowflake :
meme syntaxe SQL, meme logique de data warehouse.
"""

import duckdb
import pandas as pd
import logging
import os

logging.basicConfig(level=logging.INFO, format="%(asctime)s [LOAD] %(message)s")
log = logging.getLogger(__name__)

# Chemin de la base de donnees locale
CHEMIN_DB = "data/beauty_warehouse.duckdb"


def obtenir_connexion(chemin_db: str = CHEMIN_DB) -> duckdb.DuckDBPyConnection:
    """Cree ou ouvre la connexion a la base DuckDB."""
    os.makedirs(os.path.dirname(chemin_db), exist_ok=True)
    conn = duckdb.connect(chemin_db)
    log.info(f"Connexion etablie : {chemin_db}")
    return conn


def creer_schemas(conn: duckdb.DuckDBPyConnection) -> None:
    """
    Creation des schemas (espaces de noms) dans le data warehouse.
    On suit la convention 3 couches : raw -> staging -> mart
    """
    conn.execute("CREATE SCHEMA IF NOT EXISTS staging")
    conn.execute("CREATE SCHEMA IF NOT EXISTS dimensions")
    conn.execute("CREATE SCHEMA IF NOT EXISTS mart")
    log.info("Schemas crees : staging, dimensions, mart")


def charger_table(
    conn: duckdb.DuckDBPyConnection,
    df: pd.DataFrame,
    schema: str,
    nom_table: str,
    remplacer: bool = True
) -> None:
    """
    Charge un DataFrame dans une table DuckDB.
    Si remplacer=True, la table est recree a chaque execution (mode full refresh).
    """
    nom_complet = f"{schema}.{nom_table}"

    if remplacer:
        conn.execute(f"DROP TABLE IF EXISTS {nom_complet}")

    conn.execute(f"CREATE TABLE {nom_complet} AS SELECT * FROM df")
    nb_lignes = conn.execute(f"SELECT COUNT(*) FROM {nom_complet}").fetchone()[0]
    log.info(f"Table chargee : {nom_complet} ({nb_lignes:,} lignes)")


def charger_tout(tables: dict) -> duckdb.DuckDBPyConnection:
    """
    Charge toutes les tables dans le data warehouse.
    Retourne la connexion pour pouvoir executer des requetes ensuite.
    """
    log.info("Debut du chargement dans DuckDB...")

    conn = obtenir_connexion()
    creer_schemas(conn)

    # Mapping : nom de table -> schema cible
    mapping_schemas = {
        "stg_produits":    "staging",
        "dim_marques":     "dimensions",
        "dim_categories":  "dimensions",
        "fait_produits":   "mart",
    }

    for nom_table, df in tables.items():
        schema = mapping_schemas.get(nom_table, "staging")
        charger_table(conn, df, schema, nom_table)

    log.info("Chargement termine.")
    return conn


def afficher_resume(conn: duckdb.DuckDBPyConnection) -> None:
    """Affiche un resume de ce qui est dans le data warehouse."""
    print("\n" + "=" * 50)
    print("RESUME DU DATA WAREHOUSE")
    print("=" * 50)

    requetes = [
        ("Nombre total de produits",  "SELECT COUNT(*) FROM mart.fait_produits"),
        ("Nombre de marques",         "SELECT COUNT(*) FROM dimensions.dim_marques"),
        ("Nombre de categories",      "SELECT COUNT(*) FROM dimensions.dim_categories"),
        ("Prix moyen global",         "SELECT ROUND(AVG(Price), 2) FROM mart.fait_produits"),
        ("Score moyen global",        "SELECT ROUND(AVG(Rank), 2) FROM mart.fait_produits"),
    ]

    for label, requete in requetes:
        try:
            resultat = conn.execute(requete).fetchone()[0]
            print(f"  {label:<30} : {resultat}")
        except Exception as e:
            print(f"  {label:<30} : erreur ({e})")

    print("=" * 50)


if __name__ == "__main__":
    # Test avec des donnees fictives
    tables_test = {
        "stg_produits": pd.DataFrame({
            "Name": ["Creme hydratante", "Serum vitamine C"],
            "Brand": ["BrandA", "BrandB"],
            "Label": ["Moisturizer", "Serum"],
            "Price": [29.90, 54.00],
            "Rank": [4.2, 4.7],
        }),
        "dim_marques": pd.DataFrame({
            "marque": ["BrandA", "BrandB"],
            "nb_produits": [1, 1],
            "prix_moyen": [29.90, 54.00],
            "score_moyen": [4.2, 4.7],
            "marque_id": [1, 2],
        }),
        "dim_categories": pd.DataFrame({
            "categorie": ["Moisturizer", "Serum"],
            "categorie_id": [1, 2],
        }),
        "fait_produits": pd.DataFrame({
            "Name": ["Creme hydratante", "Serum vitamine C"],
            "Brand": ["BrandA", "BrandB"],
            "Label": ["Moisturizer", "Serum"],
            "Price": [29.90, 54.00],
            "Rank": [4.2, 4.7],
            "segment_prix": ["milieu_de_gamme", "premium"],
            "score_popularite": [0.84, 0.94],
            "est_premium": [0, 0],
        }),
    }

    conn = charger_tout(tables_test)
    afficher_resume(conn)
    conn.close()
