# Operator guide

## Import and recovery

1. Configure and migrate a dedicated database as described in the README.
2. Obtain a corrected GUIDE extract and retain its schema and manifest.
3. Run `guide-import --csv-dir /path/to/csv --tenant-id UUID --dry-run
   --json-output`. The command exits nonzero on validation errors.
4. Inspect the aggregate quality counts and fix source errors. A dry run does
   not persist imported rows or an audit entry.
5. Run the same command without `--dry-run`, and retain the JSON output and
   audit ID. Protect the output and database according to your data policy.

Failures roll back all data in that run. Audit records persist independently
after a failure where possible. If a failure audit cannot be saved, the command
reports a warning. A repeated import into the same keys fails; incremental
upsert, refresh, automatic deletion and duplicate skipping are not implemented.
Back up the database before migrations and operational imports.

Example audit query:

```sql
SELECT import_id, started_at, completed_at, status, total_records, failed_records
FROM guide_public.import_audit_trail
ORDER BY started_at DESC;
```

## Advisor query example

Always supply the tenant boundary when joining tenant-scoped entities. The
extract's degree-plan item relation also needs the revision key:

```sql
SELECT p."PersonIdentifier", p."LearnerDegreePlanIdentifier",
       i."LearnerDegreePlanItemIdentifier"
FROM guide_public."LearnerDegreePlan" AS p
JOIN guide_public."LearnerDegreePlanItem" AS i
  ON i."TenantIdentifier" = p."TenantIdentifier"
 AND i."LearnerDegreePlanIdentifier" = p."LearnerDegreePlanIdentifier"
 AND i."LearnerDegreePlanRevisionIdentifier" = p."RevisionIdentifier"
WHERE p."TenantIdentifier" = :tenant_id
  AND p."PersonIdentifier" = :person_id
  AND p."DeletedDate" IS NULL AND i."DeletedDate" IS NULL;
```

## Limitations

The dictionary supplies relational structure, not every advisor business rule.
Quality completeness counts do not validate score semantics, general temporal
ordering, or degree requirements. No row-level security, automated operator authentication,
retry policy, incremental updates, per-row recovery, full domain-specific
repositories, or performance SLA is claimed. Empty CSV fields use PostgreSQL
CSV COPY null semantics; quoted empty strings remain empty strings. The full
dataset has not passed validation until the source issues in the README are
corrected and a dry run completes.
