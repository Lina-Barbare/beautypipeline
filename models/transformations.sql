-- ============================================================
-- BeautyPipeline - Modeles SQL (style DBT)
-- ============================================================
-- Ces requetes representent la couche de transformation SQL
-- qu'on construirait avec DBT en production.
-- Chaque modele lit depuis la couche precedente et produit
-- une table propre pour la couche suivante.
-- ============================================================


-- ------------------------------------------------------------
-- MODELE 1 : Staging des produits
-- Nettoyage minimal, renommage des colonnes en snake_case
-- ------------------------------------------------------------
CREATE OR REPLACE VIEW staging.stg_produits_clean AS
SELECT
    Name          AS nom_produit,
    Brand         AS marque,
    Label         AS categorie,
    Price         AS prix,
    Rank          AS score,
    segment_prix,
    score_popularite,
    est_premium,
    nb_ingredients
FROM staging.stg_produits
WHERE prix IS NOT NULL
  AND score IS NOT NULL
  AND nom_produit IS NOT NULL;


-- ------------------------------------------------------------
-- MODELE 2 : Analyse par marque
-- Agregats utiles pour comprendre le positionnement des marques
-- ------------------------------------------------------------
CREATE OR REPLACE VIEW mart.analyse_marques AS
SELECT
    marque,
    nb_produits,
    ROUND(prix_moyen, 2)   AS prix_moyen,
    ROUND(score_moyen, 2)  AS score_moyen,
    CASE
        WHEN prix_moyen < 20  THEN 'budget'
        WHEN prix_moyen < 50  THEN 'milieu_de_gamme'
        WHEN prix_moyen < 100 THEN 'premium'
        ELSE 'luxe'
    END AS positionnement,
    RANK() OVER (ORDER BY score_moyen DESC) AS rang_score,
    RANK() OVER (ORDER BY nb_produits DESC) AS rang_catalogue
FROM dimensions.dim_marques
ORDER BY score_moyen DESC;


-- ------------------------------------------------------------
-- MODELE 3 : Analyse par categorie
-- Quelle categorie a les meilleurs produits ?
-- ------------------------------------------------------------
CREATE OR REPLACE VIEW mart.analyse_categories AS
SELECT
    Label                              AS categorie,
    COUNT(*)                           AS nb_produits,
    ROUND(AVG(Price), 2)               AS prix_moyen,
    ROUND(AVG(Rank), 2)                AS score_moyen,
    ROUND(MIN(Price), 2)               AS prix_min,
    ROUND(MAX(Price), 2)               AS prix_max,
    COUNT(CASE WHEN est_premium = 1
          THEN 1 END)                  AS nb_produits_premium,
    ROUND(COUNT(CASE WHEN est_premium = 1
          THEN 1 END) * 100.0
          / COUNT(*), 1)               AS pct_premium
FROM mart.fait_produits
GROUP BY Label
ORDER BY score_moyen DESC;


-- ------------------------------------------------------------
-- MODELE 4 : Top produits par categorie
-- Les 5 meilleurs produits de chaque categorie selon le score
-- ------------------------------------------------------------
CREATE OR REPLACE VIEW mart.top_produits_par_categorie AS
SELECT
    Label     AS categorie,
    Name      AS produit,
    Brand     AS marque,
    Price     AS prix,
    Rank      AS score,
    segment_prix,
    ROW_NUMBER() OVER (
        PARTITION BY Label
        ORDER BY Rank DESC, Price ASC
    ) AS rang_dans_categorie
FROM mart.fait_produits
QUALIFY rang_dans_categorie <= 5
ORDER BY categorie, rang_dans_categorie;


-- ------------------------------------------------------------
-- MODELE 5 : Matrice prix / score
-- Aide a identifier les produits "bonne affaire" :
-- score eleve + prix bas
-- ------------------------------------------------------------
CREATE OR REPLACE VIEW mart.matrice_prix_score AS
SELECT
    Name         AS produit,
    Brand        AS marque,
    Label        AS categorie,
    Price        AS prix,
    Rank         AS score,
    segment_prix,
    CASE
        WHEN Rank >= 4.0 AND Price < 30  THEN 'bonne_affaire'
        WHEN Rank >= 4.0 AND Price >= 60 THEN 'premium_justifie'
        WHEN Rank < 3.0  AND Price >= 60 THEN 'surpaye'
        ELSE 'standard'
    END AS profil_rapport_qualite_prix
FROM mart.fait_produits
ORDER BY score DESC, prix ASC;
