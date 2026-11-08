"""Validate CSV inventory and headers without logging row contents."""

import csv
import json
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from uuid import UUID

from src.core.model import Object


@dataclass(frozen=True)
class Inventory:
    files: list[Path]
    quality_counts: dict[str, dict[str, int]]


def discover(directory: Path, objects: dict[str, Object], tenant_id: str | None) -> Inventory:
    if not directory.is_dir():
        raise ValueError("CSV directory does not exist")
    files = sorted(directory.glob("*.csv"))
    if not files:
        raise ValueError("CSV directory contains no CSV files")
    unknown = {f.stem for f in files} - objects.keys()
    if unknown:
        raise ValueError("CSV directory contains unrecognized object names")
    manifest_path = directory.parent / "manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        expected = objects.keys() - set(manifest["omitted_objects"])
        if {f.stem for f in files} != expected:
            raise ValueError("CSV inventory does not match the extract manifest")
    if tenant_id is not None:
        try:
            tenant_id = str(UUID(tenant_id))
        except ValueError as exc:
            raise ValueError("tenant-id must be a UUID") from exc
    invalid_booleans: Counter[tuple[str, str]] = Counter()
    invalid_periods: Counter[str] = Counter()
    quality_counts: dict[str, dict[str, int]] = {}
    valid_booleans = {"true", "false", "t", "f", "yes", "no", "y", "n", "on", "off", "1", "0"}
    for path in files:
        with path.open(encoding="utf-8-sig", newline="") as stream:
            reader = csv.reader(stream, strict=True)
            header = next(reader, None)
            expected_columns = [c.name for c in objects[path.stem].columns]
            if header != expected_columns:
                raise ValueError(f"{path.name}: CSV header does not match GUIDE schema")
            tenant_index = expected_columns.index("TenantIdentifier") if (
                tenant_id is not None and "TenantIdentifier" in expected_columns
            ) else None
            boolean_columns = [(i, c.name) for i, c in enumerate(objects[path.stem].columns)
                               if c.data_type == "Boolean (bool)"]
            quality_columns = [(i, c.name) for i, c in enumerate(objects[path.stem].columns)
                               if c.name.endswith("Quality")]
            period_indexes = (
                (expected_columns.index("RecordStartDate"), expected_columns.index("RecordEndDate"))
                if {"RecordStartDate", "RecordEndDate"}.issubset(expected_columns) else None
            )
            for _, name in quality_columns:
                quality_counts[f"{path.stem}.{name}"] = {"present": 0, "missing": 0}
            for line, row in enumerate(reader, 2):
                if len(row) != len(header):
                    raise ValueError(f"{path.name}: malformed row at line {line}")
                if tenant_index is not None and row[tenant_index] != tenant_id:
                    raise ValueError(f"{path.name}: tenant mismatch at line {line}")
                for index, name in boolean_columns:
                    if row[index] and row[index].lower() not in valid_booleans:
                        invalid_booleans[(path.stem, name)] += 1
                for index, name in quality_columns:
                    bucket = "present" if row[index] else "missing"
                    quality_counts[f"{path.stem}.{name}"][bucket] += 1
                if period_indexes:
                    start, end = (row[i] for i in period_indexes)
                    if start and end:
                        try:
                            if datetime.fromisoformat(end) <= datetime.fromisoformat(start):
                                invalid_periods[path.stem] += 1
                        except (ValueError, TypeError):
                            invalid_periods[path.stem] += 1
    errors = []
    if invalid_booleans:
        details = "; ".join(f"{table}.{column}: {count}" for (table, column), count
                            in sorted(invalid_booleans.items()))
        errors.append(f"Invalid boolean values (table.column: count): {details}")
    if invalid_periods:
        details = "; ".join(f"{table}: {count}" for table, count in sorted(invalid_periods.items()))
        errors.append(f"Invalid record date ranges (table: count): {details}")
    if errors:
        raise ValueError("; ".join(errors))
    return Inventory(files, quality_counts)
