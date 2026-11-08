# GUIDE data import

Imports GUIDE v1.0.0 CSV extracts into PostgreSQL using the supplied GUIDE
data dictionary. The domain model and import port are framework-independent;
PostgreSQL COPY, CSV validation and the CLI are infrastructure adapters.

## Setup

Python 3.11+ and PostgreSQL 15+ are required. The supplied Compose file uses
an external Docker network and increases PostgreSQL's lock capacity for the
500-table schema; create the network once if it does not exist:

```sh
docker network create postgres
docker compose -f dockerCompose/docker-compose.yaml up -d postgres
docker compose -f dockerCompose/docker-compose.yaml exec postgres \
  createdb -U postgres guide_db
python -m pip install -e '.[test]'
```

Set `DATABASE_URL` to a SQLAlchemy PostgreSQL URL using the user and password
configured in the Compose file, for example
`postgresql+psycopg2://USER:PASSWORD@localhost:5432/guide_db`. Percent-encode
special characters in the user and password. Do not commit credentials or
include them in shell history. `.env.example` documents the variable; the
application does not automatically load `.env`.

```sh
alembic upgrade head
guide-import --dry-run --json-output
guide-import --json-output
```

`--csv-dir` selects another extract, and `--tenant-id UUID` requires every
tenant-scoped input row to have that tenant. The default directory is the
supplied extract. A neighboring `manifest.json`, when present, is checked
against the full inventory. Use `guide-import --help` for all options.
Keep the supplied schema JSON at its existing path: migration 001 checks its
SHA-256 to prevent silently changing the versioned schema. Make a new migration
for schema changes. Non-Compose PostgreSQL deployments should also configure
adequate `max_locks_per_transaction` (the Compose service uses 512) before
running migrations or the import.

## Current extract

The provided files contain invalid values for two nullable boolean columns:
`PersonDemographics.EmancipatedMinor` has 828 `Not Selected` values, and
`LearnerCredential.GradePointAverageOfficialIndicator` has 250 `TrueFalse`
values. **The import rejects these values**; it does not infer replacements.
Correct the source extract before importing. Other data issues may become
visible after those corrections. No source rows have been loaded into
`guide_db` by the attempted import.

## Operation

- The migration creates all 500 dictionary objects in `guide_public`, including
  objects omitted from the extract, with original quoted table/column names,
  typed columns, composite primary keys, and deferred foreign keys. Shared
  reference-code tables have the global keys defined by the dictionary;
  tenant-scoped foreign keys include the tenant.
- All supplied files are checked for matching headers, malformed rows, invalid
  boolean values, invalid `RecordStartDate`/`RecordEndDate` ranges and, if
  requested, tenant mismatches. Remaining type, required field, duplicate key
  and foreign-key checks are enforced by PostgreSQL.
- COPY and constraint validation run in one transaction. Any error rolls back
  all data from that run. A dry run executes the same database checks and rolls
  back without writing an audit record. Imports are insert-only: an existing
  primary key causes a failure, not an update or silent skip.
- Successful and failed non-dry runs write `guide_public.import_audit_trail`
  when the database is reachable. A failure to write it is reported. JSON
  output includes per-table row counts and present/missing counts for input
  columns ending in `Quality`; these are completeness counts, not a judgment
  of the validity of quality codes. `records_failed` is the number of failed
  import attempts, not a count of individual bad rows.
- Database diagnostic output intentionally excludes source values. PostgreSQL
  server logs can still contain sensitive data and must be configured and
  protected accordingly. `--tenant-id` validates the input; it is **not**
  authorization or row-level security. Restrict database credentials and
  access independently, including to audit records and shared lookup tables.

See [Operator guide](docs/OPERATOR_GUIDE.md) for examples and limitations.

## Tests

```sh
pytest -q
```

Integration tests are skipped unless `TEST_DATABASE_URL` points to a separate
disposable database already migrated with `alembic upgrade head`. They insert
test data into that database. Never point them at a production database.
