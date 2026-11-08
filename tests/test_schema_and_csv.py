import csv

import pytest

from src.core.model import Column, Object
from src.infrastructure.csv_reader import discover
from src.infrastructure.schema import build_metadata, load_model


def write_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8") as stream:
        csv.writer(stream).writerows(rows)


def test_real_schema_has_tenant_scoped_and_composite_references():
    metadata = build_metadata(load_model())
    assert len(metadata.tables) == 500
    enrollment = metadata.tables["guide_public.Enrollment"]
    person_fk = next(fk for fk in enrollment.foreign_key_constraints
                     if fk.referred_table.name == "PersonLookup")
    assert [c.name for c in person_fk.columns] == ["TenantIdentifier", "PersonIdentifier"]
    item = metadata.tables["guide_public.LearnerDegreePlanItem"]
    plan_fk = next(fk for fk in item.foreign_key_constraints
                   if fk.referred_table.name == "LearnerDegreePlan")
    assert len(plan_fk.columns) == 3
    assert plan_fk.deferrable and plan_fk.initially == "DEFERRED"


def test_csv_rejects_all_invalid_booleans_without_values(tmp_path):
    objects = {"A": Object("A", (Column("flag", "Boolean (bool)", True, False, None),)),
               "B": Object("B", (Column("flag", "Boolean (bool)", True, False, None),))}
    write_csv(tmp_path / "A.csv", [["flag"], ["Not Selected"], ["Not Selected"]])
    write_csv(tmp_path / "B.csv", [["flag"], ["TrueFalse"]])
    with pytest.raises(ValueError) as error:
        discover(tmp_path, objects, None)
    assert "A.flag: 2" in str(error.value)
    assert "B.flag: 1" in str(error.value)
    assert "Not Selected" not in str(error.value)


def test_csv_validates_headers_and_tenants(tmp_path):
    objects = {"Tenant": Object("Tenant", (
        Column("TenantIdentifier", "UUID", False, True, None),
        Column("active", "Boolean (bool)", False, False, None),
    ))}
    path = tmp_path / "Tenant.csv"
    tenant = "a3b1799d-1c80-4066-abdd-3eb146685257"
    write_csv(path, [["TenantIdentifier", "active"], [tenant, "yes"]])
    assert discover(tmp_path, objects, tenant).files == [path]
    with pytest.raises(ValueError, match="tenant mismatch"):
        discover(tmp_path, objects, "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
    write_csv(path, [["active", "TenantIdentifier"], ["yes", tenant]])
    with pytest.raises(ValueError, match="header"):
        discover(tmp_path, objects, None)


def test_csv_detects_manifest_missing_file(tmp_path):
    directory = tmp_path / "csv"
    directory.mkdir()
    write_csv(directory / "A.csv", [["flag"], ["true"]])
    (tmp_path / "manifest.json").write_text('{"omitted_objects": []}', encoding="utf-8")
    column = Column("flag", "Boolean (bool)", False, False, None)
    with pytest.raises(ValueError, match="inventory"):
        discover(directory, {"A": Object("A", (column,)), "B": Object("B", (column,))}, None)


def test_quality_report_counts_only_input_rows(tmp_path):
    objects = {"A": Object("A", (Column("NameDataQuality", "String (str or text)",
                                        True, False, None),))}
    write_csv(tmp_path / "A.csv", [["NameDataQuality"], ["complete"], [""]])
    inventory = discover(tmp_path, objects, None)
    assert inventory.quality_counts == {"A.NameDataQuality": {"present": 1, "missing": 1}}


def test_invalid_effective_date_range_is_reported(tmp_path):
    objects = {"A": Object("A", (
        Column("RecordStartDate", "Datetime", True, False, None),
        Column("RecordEndDate", "Datetime", True, False, None),
    ))}
    write_csv(tmp_path / "A.csv", [["RecordStartDate", "RecordEndDate"],
                                  ["2024-01-02", "2024-01-01"]])
    with pytest.raises(ValueError, match="Invalid record date ranges.*A: 1"):
        discover(tmp_path, objects, None)
