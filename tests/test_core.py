from datetime import date

from src.core.model import ImportCommand, ImportResult, Person
from src.core.use_cases import ImportGuide


def test_person_temporal_activity():
    person = Person("tenant", "person", record_start_date=date(2020, 1, 1),
                    record_end_date=date(2022, 1, 1), deleted_date=date(2021, 6, 1))
    assert not person.is_active(date(2019, 12, 31))
    assert person.is_active(date(2021, 5, 31))
    assert not person.is_active(date(2021, 6, 1))


def test_use_case_delegates_command():
    expected = ImportResult(success=True, import_id="test")

    class Repository:
        def import_data(self, command):
            assert command.csv_directory == "input"
            return expected

    assert ImportGuide(Repository()).execute(ImportCommand("input")) is expected
