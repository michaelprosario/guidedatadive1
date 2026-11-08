import json
from dataclasses import asdict
from pathlib import Path

import click
from sqlalchemy.exc import SQLAlchemyError

from src.core.model import ImportCommand
from src.core.use_cases import ImportGuide
from src.infrastructure.import_repository import PostgresImportRepository
from src.infrastructure.schema import ROOT


@click.command()
@click.option("--csv-dir", type=click.Path(path_type=Path, file_okay=False),
              default=ROOT / "2026-11 DevFest Florida/GUIDE Materials/csv", show_default=True)
@click.option("--database-url", envvar="DATABASE_URL", required=True,
              help="PostgreSQL SQLAlchemy URL; preferably set DATABASE_URL.")
@click.option("--tenant-id", help="Require every tenant-scoped input row to belong to this UUID.")
@click.option("--dry-run", is_flag=True, help="Validate the entire import and roll it back.")
@click.option("--json-output", is_flag=True, help="Print a machine-readable result.")
def main(csv_dir: Path, database_url: str, tenant_id: str | None,
         dry_run: bool, json_output: bool) -> None:
    """Import a GUIDE extract into the migrated PostgreSQL database."""
    try:
        repository = PostgresImportRepository(database_url)
    except (ValueError, SQLAlchemyError):
        raise click.ClickException("Invalid PostgreSQL database URL") from None
    try:
        result = ImportGuide(repository).execute(ImportCommand(str(csv_dir), tenant_id, dry_run))
    finally:
        repository.close()
    if json_output:
        click.echo(json.dumps(asdict(result), sort_keys=True))
    else:
        status = "validated (rolled back)" if result.success and dry_run else (
            "imported" if result.success else "failed"
        )
        click.echo(f"Import {status}: {result.records_processed} rows in "
                   f"{result.duration_seconds:.1f}s; audit ID {result.import_id}")
        for error in result.errors:
            click.echo(f"Error: {error}", err=True)
        for warning in result.warnings:
            click.echo(f"Warning: {warning}", err=True)
    if not result.success:
        raise click.exceptions.Exit(1)


if __name__ == "__main__":
    main()
