"""
BeautyPipeline - Tests de qualite des donnees
===============================================
Tests automatiques pour verifier l'integrite
des donnees a chaque execution du pipeline.
Inspire des tests DBT (not_null, unique, accepted_values...).
"""

import duckdb
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [QUALITY] %(message)s")
log = logging.getLogger(__name__)


class TestQualite:
    """
    Classe qui execute des tests de qualite sur les tables
    du data warehouse et retourne un rapport.
    """

    def __init__(self, conn: duckdb.DuckDBPyConnection):
        self.conn = conn
        self.resultats = []

    def _executer_test(self, nom: str, requete: str, seuil_max_erreurs: int = 0) -> bool:
        """Execute un test et enregistre le resultat."""
        try:
            nb_erreurs = self.conn.execute(requete).fetchone()[0]
            succes = nb_erreurs <= seuil_max_erreurs
            statut = "PASS" if succes else "FAIL"
            self.resultats.append({
                "test": nom,
                "statut": statut,
                "nb_erreurs": nb_erreurs
            })
            log.info(f"[{statut}] {nom} ({nb_erreurs} erreur(s))")
            return succes
        except Exception as e:
            self.resultats.append({"test": nom, "statut": "ERROR", "nb_erreurs": -1})
            log.error(f"[ERROR] {nom} : {e}")
            return False

    # ----------------------------------------------------------
    # Tests de type "not_null" : verifier qu'une colonne ne
    # contient pas de valeurs manquantes
    # ----------------------------------------------------------
    def test_not_null_nom_produit(self):
        return self._executer_test(
            "not_null: nom_produit",
            "SELECT COUNT(*) FROM mart.fait_produits WHERE Name IS NULL"
        )

    def test_not_null_marque(self):
        return self._executer_test(
            "not_null: marque",
            "SELECT COUNT(*) FROM mart.fait_produits WHERE Brand IS NULL"
        )

    def test_not_null_prix(self):
        return self._executer_test(
            "not_null: prix",
            "SELECT COUNT(*) FROM mart.fait_produits WHERE Price IS NULL"
        )

    # ----------------------------------------------------------
    # Tests de plage de valeurs : verifier que les valeurs
    # numeriques sont dans des bornes coherentes
    # ----------------------------------------------------------
    def test_prix_positif(self):
        return self._executer_test(
            "range: prix > 0",
            "SELECT COUNT(*) FROM mart.fait_produits WHERE Price <= 0"
        )

    def test_score_entre_0_et_5(self):
        return self._executer_test(
            "range: score entre 0 et 5",
            "SELECT COUNT(*) FROM mart.fait_produits WHERE Rank < 0 OR Rank > 5"
        )

    def test_score_popularite_entre_0_et_1(self):
        return self._executer_test(
            "range: score_popularite entre 0 et 1",
            "SELECT COUNT(*) FROM mart.fait_produits WHERE score_popularite < 0 OR score_popularite > 1"
        )

    # ----------------------------------------------------------
    # Tests de valeurs acceptees : verifier que les categories
    # contiennent uniquement des valeurs connues
    # ----------------------------------------------------------
    def test_segment_prix_valide(self):
        valeurs_valides = "('budget', 'milieu_de_gamme', 'premium', 'luxe', 'inconnu')"
        return self._executer_test(
            "accepted_values: segment_prix",
            f"SELECT COUNT(*) FROM mart.fait_produits WHERE segment_prix NOT IN {valeurs_valides}"
        )

    def test_est_premium_binaire(self):
        return self._executer_test(
            "accepted_values: est_premium (0 ou 1)",
            "SELECT COUNT(*) FROM mart.fait_produits WHERE est_premium NOT IN (0, 1)"
        )

    # ----------------------------------------------------------
    # Tests de coherence metier : logique specifique au domaine
    # ----------------------------------------------------------
    def test_coherence_premium_prix(self):
        """Un produit marque premium doit avoir un prix > 60."""
        return self._executer_test(
            "coherence: produit premium => prix > 60",
            "SELECT COUNT(*) FROM mart.fait_produits WHERE est_premium = 1 AND Price <= 60",
            seuil_max_erreurs=0
        )

    def test_dimensions_non_vides(self):
        return self._executer_test(
            "not_empty: dim_marques",
            "SELECT CASE WHEN COUNT(*) = 0 THEN 1 ELSE 0 END FROM dimensions.dim_marques"
        )

    # ----------------------------------------------------------
    # Execution de tous les tests
    # ----------------------------------------------------------
    def executer_tous(self) -> dict:
        """Lance tous les tests et retourne le rapport final."""
        log.info("Debut des tests de qualite...")

        tests = [
            self.test_not_null_nom_produit,
            self.test_not_null_marque,
            self.test_not_null_prix,
            self.test_prix_positif,
            self.test_score_entre_0_et_5,
            self.test_score_popularite_entre_0_et_1,
            self.test_segment_prix_valide,
            self.test_est_premium_binaire,
            self.test_coherence_premium_prix,
            self.test_dimensions_non_vides,
        ]

        for test in tests:
            test()

        nb_total  = len(self.resultats)
        nb_pass   = sum(1 for r in self.resultats if r["statut"] == "PASS")
        nb_fail   = sum(1 for r in self.resultats if r["statut"] == "FAIL")
        nb_error  = sum(1 for r in self.resultats if r["statut"] == "ERROR")

        rapport = {
            "total": nb_total,
            "pass": nb_pass,
            "fail": nb_fail,
            "error": nb_error,
            "taux_reussite": round(nb_pass / nb_total * 100, 1),
            "details": self.resultats
        }

        print("\n" + "=" * 50)
        print("RAPPORT QUALITE DES DONNEES")
        print("=" * 50)
        print(f"  Tests executes : {nb_total}")
        print(f"  Reussis        : {nb_pass}")
        print(f"  Echoues        : {nb_fail}")
        print(f"  Erreurs        : {nb_error}")
        print(f"  Taux de reussite : {rapport['taux_reussite']}%")
        print("=" * 50)

        if nb_fail > 0:
            print("\nTests en echec :")
            for r in self.resultats:
                if r["statut"] == "FAIL":
                    print(f"  - {r['test']} ({r['nb_erreurs']} probleme(s))")

        return rapport
