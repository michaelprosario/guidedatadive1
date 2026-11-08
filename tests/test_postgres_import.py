import csv
import os
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from src.core.model import ImportCommand
from src.infrastructure.import_repository import PostgresImportRepository
from src.infrastructure.schema import load_model

pytestmark = pytest.mark.integration


@pytest.fixture
def database_url():
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("set TEST_DATABASE_URL to a migrated disposable PostgreSQL database")
    return url


def make_files(directory, tenant, source_tenant=None):
    objects = load_model()
    data = {
        "Tenant": {"TenantIdentifier": tenant, "TenantName": "Test",
                   "ActiveIndicator": "true", "CreatedDate": "2024-01-01T00:00:00Z"},
        "SourceSystemLookup": {"TenantIdentifier": source_tenant or tenant,
                               "SourceSystemIdentifier": str(uuid4()), "Name": "Test",
                               "Status": "Active", "CreatedBy": "1",
                               "CreatedDate": "2024-01-01T00:00:00Z"},
    }
    for name, values in data.items():
        with (directory / f"{name}.csv").open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=[c.name for c in objects[name].columns])
            writer.writeheader()
            writer.writerow(values)


def count(engine, table, column, value):
    with engine.connect() as conn:
        return conn.execute(text(f'SELECT count(*) FROM guide_public."{table}" WHERE '
                                 f'"{column}" = :value'), {"value": value}).scalar_one()


def test_import_dry_run_commit_duplicate_and_audit(database_url, tmp_path):
    tenant = str(uuid4())
    make_files(tmp_path, tenant)
    repository = PostgresImportRepository(database_url)
    engine = create_engine(database_url)
    try:
        dry = repository.import_data(ImportCommand(str(tmp_path), tenant, True))
        assert dry.success and dry.records_processed == 2
        assert count(engine, "Tenant", "TenantIdentifier", tenant) == 0
        assert count(engine, "import_audit_trail", "import_id", dry.import_id) == 0
        result = repository.import_data(ImportCommand(str(tmp_path), tenant))
        assert result.success and result.records_processed == 2
        assert count(engine, "Tenant", "TenantIdentifier", tenant) == 1
        assert count(engine, "import_audit_trail", "import_id", result.import_id) == 1
        duplicate = repository.import_data(ImportCommand(str(tmp_path), tenant))
        assert not duplicate.success and duplicate.records_failed == 1
        assert count(engine, "import_audit_trail", "import_id", duplicate.import_id) == 1
        assert count(engine, "Tenant", "TenantIdentifier", tenant) == 1
    finally:
        repository.close()
        engine.dispose()


def test_missing_foreign_key_rolls_back(database_url, tmp_path):
    tenant = str(uuid4())
    make_files(tmp_path, tenant, str(uuid4()))
    repository = PostgresImportRepository(database_url)
    engine = create_engine(database_url)
    try:
        result = repository.import_data(ImportCommand(str(tmp_path)))
        assert not result.success and "23503" in result.errors[0]
        assert count(engine, "Tenant", "TenantIdentifier", tenant) == 0
        assert count(engine, "import_audit_trail", "import_id", result.import_id) == 1
    finally:
        repository.close()
        engine.dispose()


def test_audit_failure_cannot_report_success(database_url, tmp_path, monkeypatch):
    tenant = str(uuid4())
    make_files(tmp_path, tenant)
    repository = PostgresImportRepository(database_url)
    engine = create_engine(database_url)

    def fail_audit(*args):
        raise SQLAlchemyError("audit failure")

    monkeypatch.setattr(repository, "_audit", fail_audit)
    try:
        result = repository.import_data(ImportCommand(str(tmp_path)))
        assert not result.success
        assert result.warnings
        assert count(engine, "Tenant", "TenantIdentifier", tenant) == 0
    finally:
        repository.close()
        engine.dispose()
