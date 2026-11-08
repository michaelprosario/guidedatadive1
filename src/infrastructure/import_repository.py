"""Transactional PostgreSQL COPY implementation of the import port."""

import getpass
import csv
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import psycopg2
from psycopg2 import sql
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from src.core.model import ImportCommand, ImportResult
from src.infrastructure.csv_reader import discover
from src.infrastructure.schema import SCHEMA, load_model


class PostgresImportRepository:
    def __init__(self, database_url: str):
        self.engine = create_engine(database_url, pool_pre_ping=True)

    def close(self) -> None:
        self.engine.dispose()

    def import_data(self, command: ImportCommand) -> ImportResult:
        started = datetime.now(timezone.utc)
        timer = time.monotonic()
        result = ImportResult(success=False, import_id=str(uuid4()))
        current_table = None
        try:
            objects = load_model()
            inventory = discover(Path(command.csv_directory), objects, command.tenant_id)
            counts: dict[str, int] = {}
            with self.engine.connect() as connection:
                transaction = connection.begin()
                try:
                    cursor = connection.connection.cursor()
                    try:
                        cursor.execute("SET CONSTRAINTS ALL DEFERRED")
                        for path in inventory.files:
                            current_table = path.stem
                            columns = [c.name for c in objects[current_table].columns]
                            statement = sql.SQL(
                                "COPY {}.{} ({}) FROM STDIN WITH (FORMAT CSV, HEADER TRUE, ENCODING 'UTF8')"
                            ).format(
                                sql.Identifier(SCHEMA), sql.Identifier(current_table),
                                sql.SQL(", ").join(map(sql.Identifier, columns)),
                            )
                            with path.open("r", encoding="utf-8-sig", newline="") as stream:
                                cursor.copy_expert(statement.as_string(cursor), stream)
                            counts[current_table] = cursor.rowcount
                        current_table = None
                        cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
                    finally:
                        cursor.close()
                    result.records_processed = sum(counts.values())
                    result.table_counts = counts
                    result.quality_counts = inventory.quality_counts
                    result.success = True
                    result.duration_seconds = time.monotonic() - timer
                    if command.dry_run:
                        transaction.rollback()
                    else:
                        self._audit(connection, command, result, started)
                        transaction.commit()
                except BaseException:
                    transaction.rollback()
                    raise
        except (ValueError, KeyError, OSError, UnicodeError, csv.Error,
                psycopg2.Error, SQLAlchemyError) as exc:
            result.success = False
            result.records_failed = 1
            result.duration_seconds = time.monotonic() - timer
            if isinstance(exc, (psycopg2.Error, SQLAlchemyError)):
                original = getattr(exc, "orig", exc)
                diag = getattr(original, "diag", None)
                constraint = getattr(diag, "constraint_name", None)
                column = getattr(diag, "column_name", None)
                table = current_table or getattr(diag, "table_name", None)
                sqlstate = getattr(original, "pgcode", None)
                detail = " (" + ", ".join(
                    part for part in (constraint, column, sqlstate) if part
                ) + ")" if constraint or column or sqlstate else ""
                result.errors.append(f"Database validation or connection failure{detail}" +
                                     (f" in {table}" if table else ""))
            else:
                result.errors.append(str(exc))
            if not command.dry_run:
                try:
                    with self.engine.begin() as connection:
                        self._audit(connection, command, result, started)
                except SQLAlchemyError:
                    result.warnings.append("Could not write failure audit record; check database connectivity and migrations")
        return result

    @staticmethod
    def _audit(connection, command: ImportCommand, result: ImportResult, started: datetime) -> None:
        connection.execute(text(f'''
            INSERT INTO "{SCHEMA}".import_audit_trail
            (import_id, started_at, completed_at, status, tenant_id, total_records,
             failed_records, validation_errors, created_by)
            VALUES (:id, :started, :completed, :status, :tenant, :total,
                    :failed, CAST(:errors AS jsonb), :operator)
        '''), {
            "id": result.import_id,
            "started": started,
            "completed": datetime.now(timezone.utc),
            "status": "success" if result.success else "failed",
            "tenant": command.tenant_id,
            "total": result.records_processed,
            "failed": result.records_failed,
            "errors": json.dumps(result.errors),
            "operator": getpass.getuser(),
        })
