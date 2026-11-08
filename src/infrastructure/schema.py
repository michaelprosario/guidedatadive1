"""Translate the versioned GUIDE data dictionary into relational metadata."""

import hashlib
import json
from collections import defaultdict
from pathlib import Path

from sqlalchemy import (
    BigInteger, Boolean, Column as SAColumn, Date, DateTime, Float,
    ForeignKeyConstraint, Integer, MetaData, Table, Text,
)
from sqlalchemy.dialects.postgresql import UUID

from src.core.model import Column, Object

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_FILE = ROOT / "2026-11 DevFest Florida/GUIDE Materials/guide_data_model_schema_v1.0.0.json"
SCHEMA = "guide_public"
SCHEMA_SHA256 = "ed2ab10674f7ab63bc1bccdd49fee5c381302b88a90567a2e242e8c97b4bb9b6"


def load_model(path: Path = SCHEMA_FILE) -> dict[str, Object]:
    content = path.read_bytes()
    if path == SCHEMA_FILE and hashlib.sha256(content).hexdigest() != SCHEMA_SHA256:
        raise ValueError("GUIDE schema differs from the version used by migration 001")
    records = json.loads(content)["sheets"]["Objects"]["records"]
    objects: dict[str, list[Column]] = defaultdict(list)
    for row in records:
        objects[row["Object"]].append(Column(
            name=row["Column"],
            data_type=row["GenericDataType"],
            nullable=row["Nullable"] == "Y",
            primary_key="PK" in (row["Key"] or ""),
            reference=row["FKReference"],
        ))
    return {name: Object(name, tuple(columns)) for name, columns in objects.items()}


def _constraint_name(source: str, target: str, columns: list[str]) -> str:
    digest = hashlib.sha256(f"{source}:{target}:{','.join(columns)}".encode()).hexdigest()[:16]
    return f"fk_{digest}"


def build_metadata(objects: dict[str, Object]) -> MetaData:
    types = {
        "String (str or text)": Text,
        "UUID": UUID,
        "Integer (bigint)": BigInteger,
        "Integer (int)": Integer,
        "Floating point (float)": Float,
        "Boolean (bool)": Boolean,
        "Date": Date,
        "Datetime": DateTime(timezone=True),
    }
    metadata = MetaData(schema=SCHEMA)
    for obj in objects.values():
        columns = [
            SAColumn(c.name, types[c.data_type], primary_key=c.primary_key, nullable=c.nullable)
            for c in obj.columns
        ]
        Table(obj.name, metadata, *columns)

    for obj in objects.values():
        grouped: dict[str, list[tuple[str, str]]] = defaultdict(list)
        for column in obj.columns:
            if column.reference:
                target, target_column = column.reference.split(".", 1)
                grouped[target].append((column.name, target_column))
        for target, refs in grouped.items():
            target_pk = [c.name for c in objects[target].columns if c.primary_key]
            non_tenant_pk = [c for c in target_pk if c != "TenantIdentifier"]
            if len(non_tenant_pk) == 1:
                relationships = [[pair] for pair in refs]
            else:
                relationships = [refs]
            for relationship in relationships:
                mapping = {remote: local for local, remote in relationship}
                if "TenantIdentifier" in target_pk and "TenantIdentifier" not in mapping:
                    if not any(c.name == "TenantIdentifier" for c in obj.columns):
                        raise ValueError(f"{obj.name} lacks tenant key for {target}")
                    mapping["TenantIdentifier"] = "TenantIdentifier"
                if set(mapping) != set(target_pk):
                    raise ValueError(f"Incomplete foreign key: {obj.name} -> {target}")
                local_columns = [mapping[c] for c in target_pk]
                metadata.tables[f"{SCHEMA}.{obj.name}"].append_constraint(
                    ForeignKeyConstraint(
                        local_columns,
                        [f"{SCHEMA}.{target}.{c}" for c in target_pk],
                        name=_constraint_name(obj.name, target, local_columns),
                        deferrable=True,
                        initially="DEFERRED",
                    )
                )
    return metadata
