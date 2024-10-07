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
        comparison = FAHDatabase.from_directory(comparison)
        comparison.report()

        comparison_report = database.compare_to_source(comparison)
        comparison_report.report()

@cli.command(help="Sync two databases")
@click.option("--source", type=Path, help="Path to the database", required=True)
@click.option("--destination", type=Path, help="Path to the database to sync to", required=True)
@click.option("--sync", is_flag=True, help="Sync the databases", default=False)
def sync(source, destination, sync):
    source = SourceDatabase.from_directory(source)
    destination = FAHDatabase.from_directory(destination)
    comparison = destination.compare_to_source(source)
    comparison.report()

    destination.sync(source, sync=sync)