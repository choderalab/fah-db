import click
from fahdb.database import SourceDatabase, FAHDatabase
from pathlib import Path

@click.group(help="Command-line interface for fahdb")
def cli(): ...


@cli.command(help="Report on a database")
@click.option("--database", type=Path, help="Path to the database", required=True)
@click.option("--comparison", type=Path, help="Path to a database to compare to the first", default=None)
@click.option("--output", type=Path, help="Path to the output file", default=None)
def report(database, comparison, output):
    database = FAHDatabase.from_directory(database)
    database.report()

    if comparison is not None:
        comparison = SourceDatabase.from_directory(comparison)
        comparison.report()

        comparison_report = database.compare_to_source(comparison)
        comparison_report.report()
