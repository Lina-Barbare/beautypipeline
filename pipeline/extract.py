"""
BeautyPipeline - Etape 1 : Extraction
======================================
Chargement et validation des donnees brutes
avant toute transformation.
"""

import pandas as pd
import os
import logging

# Configuration des logs
logging.basicConfig(level=logging.INFO, format="%(asctime)s [EXTRACT] %(message)s")
log = logging.getLogger(__name__)


def charger_csv(chemin: str) -> pd.DataFrame:
    """Charge le fichier CSV brut et verifie qu'il existe."""
    if not os.path.exists(chemin):
        raise FileNotFoundError(f"Fichier introuvable : {chemin}")

    df = pd.read_csv(chemin)
    log.info(f"Fichier charge : {chemin}")
    log.info(f"Dimensions : {df.shape[0]:,} lignes x {df.shape[1]} colonnes")
    return df


def valider_schema(df: pd.DataFrame, colonnes_attendues: list) -> bool:
    """Verifie que toutes les colonnes attendues sont presentes."""
    colonnes_manquantes = [c for c in colonnes_attendues if c not in df.columns]

    if colonnes_manquantes:
        log.warning(f"Colonnes manquantes : {colonnes_manquantes}")
        log.info(f"Colonnes disponibles : {list(df.columns)}")
        return False

    log.info("Schema valide : toutes les colonnes attendues sont presentes")
    return True


def profiler_donnees(df: pd.DataFrame) -> dict:
    """
    Genere un profil rapide du dataset :
    - valeurs manquantes par colonne
    - nombre de doublons
    - types de donnees
    """
    profil = {
        "nb_lignes": len(df),
        "nb_colonnes": len(df.columns),
        "doublons": df.duplicated().sum(),
        "valeurs_manquantes": df.isnull().sum().to_dict(),
        "types": df.dtypes.astype(str).to_dict(),
    }

    log.info(f"Doublons detectes : {profil['doublons']}")
    total_manquants = sum(profil["valeurs_manquantes"].values())
    log.info(f"Total valeurs manquantes : {total_manquants}")

    return profil


def extraire(chemin_csv: str) -> tuple[pd.DataFrame, dict]:
    """
    Fonction principale d'extraction.
    Retourne les donnees brutes et leur profil.
    """
    log.info("Debut de l'extraction...")

    # Colonnes qu'on attend dans le dataset cosmetiques Kaggle
    colonnes_attendues = ["Label", "Brand", "Name", "Price", "Rank", "Ingredients"]

    df = charger_csv(chemin_csv)
    valider_schema(df, colonnes_attendues)
    profil = profiler_donnees(df)

    log.info("Extraction terminee.")
    return df, profil


if __name__ == "__main__":
    df, profil = extraire("data/cosmetics.csv")
    print("\nApercu des donnees brutes :")
    print(df.head(3))
    print("\nProfil :")
    for cle, val in profil.items():
        if cle != "valeurs_manquantes":
            print(f"  {cle} : {val}")
