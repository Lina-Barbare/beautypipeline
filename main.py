import time
import sys
import duckdb
import logging

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich import box
from rich.rule import Rule

from pipeline.extract import extraire
from pipeline.transform import transformer
from pipeline.load import charger_tout
from tests.quality_checks import TestQualite

logging.disable(logging.CRITICAL)

console = Console()

CHEMIN_CSV = "data/cosmetics.csv"
CHEMIN_DB  = "data/beauty_warehouse.duckdb"


def executer_modeles_sql(conn: duckdb.DuckDBPyConnection) -> int:
    with open("models/transformations.sql", "r", encoding="utf-8") as f:
        contenu = f.read()

    lignes = [l for l in contenu.splitlines() if not l.strip().startswith("--")]
    sql_propre = "\n".join(lignes)
    instructions = [s.strip() for s in sql_propre.split(";") if len(s.strip()) > 20]

    nb_ok = 0
    for instruction in instructions:
        try:
            conn.execute(instruction)
            nb_ok += 1
        except Exception:
            pass
    return nb_ok


def afficher_resultats(conn: duckdb.DuckDBPyConnection) -> None:

    console.print(Rule("[bold green]Top 5 marques par score[/bold green]"))
    try:
        res = conn.execute("""
            SELECT marque, nb_produits, prix_moyen, score_moyen, positionnement
            FROM mart.analyse_marques LIMIT 5
        """).fetchdf()

        table = Table(box=box.ROUNDED, show_header=True, header_style="bold cyan")
        table.add_column("Marque",         style="white",   min_width=18)
        table.add_column("Produits",       style="cyan",    justify="right")
        table.add_column("Prix moyen",     style="yellow",  justify="right")
        table.add_column("Score",          style="green",   justify="right")
        table.add_column("Positionnement", style="magenta")

        for _, row in res.iterrows():
            table.add_row(
                str(row["marque"]),
                str(int(row["nb_produits"])),
                f"{row['prix_moyen']:.2f} $",
                f"{row['score_moyen']:.2f} / 5",
                str(row["positionnement"]),
            )
        console.print(table)
    except Exception as e:
        console.print(f"[red]Erreur : {e}[/red]")

    console.print(Rule("[bold green]Categories par score moyen[/bold green]"))
    try:
        res = conn.execute("""
            SELECT categorie, nb_produits, prix_moyen, score_moyen, pct_premium
            FROM mart.analyse_categories ORDER BY score_moyen DESC
        """).fetchdf()

        table2 = Table(box=box.ROUNDED, show_header=True, header_style="bold cyan")
        table2.add_column("Categorie",  style="white",   min_width=14)
        table2.add_column("Produits",   style="cyan",    justify="right")
        table2.add_column("Prix moyen", style="yellow",  justify="right")
        table2.add_column("Score",      style="green",   justify="right")
        table2.add_column("% Premium",  style="magenta", justify="right")

        for _, row in res.iterrows():
            table2.add_row(
                str(row["categorie"]),
                str(int(row["nb_produits"])),
                f"{row['prix_moyen']:.2f} $",
                f"{row['score_moyen']:.2f} / 5",
                f"{row['pct_premium']:.1f} %",
            )
        console.print(table2)
    except Exception as e:
        console.print(f"[red]Erreur : {e}[/red]")

    console.print(Rule("[bold green]Repartition par segment de prix[/bold green]"))
    try:
        res = conn.execute("""
            SELECT segment_prix,
                   COUNT(*) AS nb_produits,
                   ROUND(AVG(Price), 2) AS prix_moyen,
                   ROUND(AVG(Rank), 2) AS score_moyen
            FROM mart.fait_produits
            GROUP BY segment_prix ORDER BY prix_moyen
        """).fetchdf()

        table3 = Table(box=box.ROUNDED, show_header=True, header_style="bold cyan")
        table3.add_column("Segment",     style="white",  min_width=16)
        table3.add_column("Produits",    style="cyan",   justify="right")
        table3.add_column("Prix moyen",  style="yellow", justify="right")
        table3.add_column("Score moyen", style="green",  justify="right")

        for _, row in res.iterrows():
            table3.add_row(
                str(row["segment_prix"]),
                str(int(row["nb_produits"])),
                f"{row['prix_moyen']:.2f} $",
                f"{row['score_moyen']:.2f} / 5",
            )
        console.print(table3)
    except Exception as e:
        console.print(f"[red]Erreur : {e}[/red]")


def afficher_tests_qualite(rapport: dict) -> None:
    console.print(Rule("[bold green]Rapport qualite des donnees[/bold green]"))

    table = Table(box=box.ROUNDED, show_header=True, header_style="bold cyan")
    table.add_column("Test",    style="white", min_width=40)
    table.add_column("Statut",  justify="center", min_width=8)
    table.add_column("Erreurs", justify="right")

    for r in rapport["details"]:
        if r["statut"] == "PASS":
            statut = "[bold green]PASS[/bold green]"
        elif r["statut"] == "FAIL":
            statut = "[bold red]FAIL[/bold red]"
        else:
            statut = "[bold yellow]ERROR[/bold yellow]"
        table.add_row(r["test"], statut, str(r["nb_erreurs"]))

    console.print(table)


def lancer_pipeline():
    debut = time.time()

    console.print(Panel.fit(
        "[bold green]BEAUTYPIPELINE[/bold green]\n"
        "[dim]Pipeline ETL — Produits cosmetiques Sephora[/dim]",
        border_style="green"
    ))

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=30),
        TextColumn("[green]{task.percentage:>3.0f}%"),
        console=console,
        transient=True
    ) as progress:

        tache = progress.add_task("Lancement...", total=4)

        progress.update(tache, description="[cyan]Extraction des donnees...[/cyan]")
        try:
            df_brut, profil = extraire(CHEMIN_CSV)
        except FileNotFoundError as e:
            console.print(f"[bold red]Erreur : {e}[/bold red]")
            sys.exit(1)
        progress.advance(tache)

        progress.update(tache, description="[cyan]Transformation des donnees...[/cyan]")
        tables = transformer(df_brut)
        progress.advance(tache)

        progress.update(tache, description="[cyan]Chargement dans DuckDB...[/cyan]")
        conn = charger_tout(tables)
        progress.advance(tache)

        progress.update(tache, description="[cyan]Modeles SQL et tests qualite...[/cyan]")
        nb_modeles = executer_modeles_sql(conn)
        tests = TestQualite(conn)
        rapport = tests.executer_tous()
        progress.advance(tache)

    afficher_tests_qualite(rapport)
    afficher_resultats(conn)

    duree = round(time.time() - debut, 2)
    console.print()

    bilan = Table(box=box.ROUNDED, show_header=False, border_style="green")
    bilan.add_column("Cle",    style="dim",        min_width=22)
    bilan.add_column("Valeur", style="bold white")

    bilan.add_row("Duree totale",     f"{duree}s")
    bilan.add_row("Produits traites", f"{profil['nb_lignes']:,}")
    bilan.add_row("Tables creees",    str(len(tables)))
    bilan.add_row("Modeles SQL",      str(nb_modeles))
    bilan.add_row("Tests qualite",    f"[green]{rapport['pass']}/{rapport['total']} passes[/green]")
    bilan.add_row("Data warehouse",   CHEMIN_DB)

    console.print(Panel(
        bilan,
        title="[bold green]Pipeline termine avec succes[/bold green]",
        border_style="green"
    ))

    conn.close()

    if rapport["fail"] > 0:
        console.print(f"[bold red]{rapport['fail']} test(s) en echec.[/bold red]")
        sys.exit(1)


if __name__ == "__main__":
    lancer_pipeline()
