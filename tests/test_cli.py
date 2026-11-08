import json

from click.testing import CliRunner

from src.cli.main import main
from src.core.model import ImportResult


def test_cli_json_output_and_dry_run(monkeypatch, tmp_path):
    class Repository:
        def __init__(self, database_url):
            assert database_url == "postgresql://test"

        def import_data(self, command):
            assert command.dry_run
            return ImportResult(success=True, import_id="test", records_processed=4)

        def close(self):
            pass

    monkeypatch.setattr("src.cli.main.PostgresImportRepository", Repository)
    result = CliRunner().invoke(main, ["--csv-dir", str(tmp_path),
                                      "--database-url", "postgresql://test",
                                      "--dry-run", "--json-output"])
    assert result.exit_code == 0
    assert json.loads(result.output)["records_processed"] == 4


def test_cli_reports_failure(monkeypatch, tmp_path):
    class Repository:
        def __init__(self, database_url):
            pass

        def import_data(self, command):
            return ImportResult(success=False, import_id="test", errors=["invalid input"])

        def close(self):
            pass

    monkeypatch.setattr("src.cli.main.PostgresImportRepository", Repository)
    result = CliRunner().invoke(main, ["--csv-dir", str(tmp_path),
                                      "--database-url", "postgresql://test"])
    assert result.exit_code == 1
    assert "invalid input" in result.output
