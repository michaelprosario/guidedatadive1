"""GUIDE metadata and import result types."""

from dataclasses import dataclass, field
from datetime import date
from typing import Mapping


@dataclass(frozen=True)
class Column:
    name: str
    data_type: str
    nullable: bool
    primary_key: bool
    reference: str | None


@dataclass(frozen=True)
class Object:
    name: str
    columns: tuple[Column, ...]


@dataclass(frozen=True)
class Person:
    tenant_id: str
    person_id: str
    first_name: str | None = None
    last_name: str | None = None
    record_start_date: date | None = None
    record_end_date: date | None = None
    deleted_date: date | None = None

    def is_active(self, as_of: date) -> bool:
        return (
            (self.record_start_date is None or self.record_start_date <= as_of)
            and (self.record_end_date is None or as_of <= self.record_end_date)
            and (self.deleted_date is None or as_of < self.deleted_date)
        )


@dataclass(frozen=True)
class ImportCommand:
    csv_directory: str
    tenant_id: str | None = None
    dry_run: bool = False


@dataclass
class ImportResult:
    success: bool
    import_id: str
    records_processed: int = 0
    records_failed: int = 0
    duration_seconds: float = 0
    table_counts: Mapping[str, int] = field(default_factory=dict)
    quality_counts: Mapping[str, Mapping[str, int]] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
