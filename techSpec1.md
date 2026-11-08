# Technical Specification: GUIDE Data Import Program

**Version:** 1.0  
**Date:** 2026-11-08  
**Status:** Draft  

---

## Executive Summary

This document outlines the technical approach for building a Python-based data import program that loads the GUIDE v1.0.0 data model CSV files into a PostgreSQL database. The program will follow clean architecture principles to ensure maintainability, testability, and extensibility for future enhancements.

---

## 1. Objectives

1. **Ingest all 116 CSV files** from `2026-11 DevFest Florida/GUIDE Materials/csv`
2. **Validate and normalize data** according to GUIDE schema specifications
3. **Populate PostgreSQL** with relational data while preserving referential integrity
4. **Support advisor workflows** as outlined in `dataModelReviewForAdvisor.md`
5. **Maintain data lineage** through source-system tracking fields (SourceSystemIdentifier, SourceSystemKeyValue, etc.)
6. **Enable incremental updates** and data quality monitoring

---

## 2. Key Observations from Research

### Data Model Characteristics (from `dataModelReviewForAdvisor.md`)

- **Multi-tenant structure**: All tables use `TenantIdentifier` as a key attribute
- **Audit trails**: Records include `CreatedBy`, `CreatedDate`, `UpdatedBy`, `UpdatedDate`, `DeletedBy`, `DeletedDate`
- **Source system lineage**: `SourceSystemIdentifier`, `SourceSystemKeyValue`, `SourceSystemCreatedDate`, `SourceSystemUpdatedDate`, `SourceSystemDeletedDate`
- **Data quality flags**: Many date and identifier fields include quality indicators (e.g., `BirthDateQuality`, `SSNDataQuality`)
- **Effective dating**: Many entities support `RecordStartDate` and `RecordEndDate` for temporal relationships
- **Rich relationships**: Complex many-to-many associations (e.g., `PersonProgramProgressEvaluation` → `PersonProgramRequirementEvaluation` → `PersonProgramRequirementEvidence`)

### High-Value Entity Groups for Advisors

1. **Person & Demographics**: PersonLookup, PersonDemographics, PersonPhone, PersonEmail, PersonAddress
2. **Academic Programs**: ProgramOfStudyLookup, ProgramRequirement, ProgramRequirementCourse, AcademicCatalog
3. **Enrollment & Progress**: Enrollment, LearnerAcademicCredit, PersonProgramProgressEvaluation, PersonProgramRequirementEvaluation
4. **Degree Planning**: LearnerDegreePlan, LearnerDegreePlanItem, LearnerDegreePlanPreferences
5. **Support & Advisement**: PersonSupportAssignment, PersonSupportReferral, PersonSuccessIndicatorScore
6. **Career & Transfer**: CareerPathway, LearnerTransferCreditEvaluation, LearnerAcademicCreditTransferEvaluation

### Reference Data Dependencies

- 27 lookup tables (e.g., `RoleLookup`, `CourseStatusLookup`, `ApplicationStatusLookup`)
- Must be loaded first to satisfy foreign key constraints
- All lookups reference `ReferenceCodeSet` and `ReferenceCodeValue`

---

## 3. Technical Architecture

### 3.1 Clean Architecture Layers

Following the principles in `specs/clean_architecture.md`, the import program is organized into four concentric layers:

#### **Layer 1: Core (Domain Logic)**
- **Location**: `src/core/`
- **Responsibility**: Business rules, entities, use cases
- **Contents**:
  - `entities/`: Domain models representing GUIDE concepts (Person, Program, Enrollment, etc.)
  - `use_cases/`: Import orchestration logic (LoadReferenceData, LoadPersonData, ValidateConsistency, etc.)
  - `ports/`: Abstract interfaces (IRepository, IDataValidator, IProgressReporter)
  - **Zero dependencies** on external frameworks or infrastructure details

#### **Layer 2: Infrastructure (Technical Implementation)**
- **Location**: `src/infrastructure/`
- **Responsibility**: Database access, CSV parsing, external concerns
- **Contents**:
  - `repositories/`: Concrete PostgreSQL implementations (PersonRepository, ProgramRepository, etc.)
  - `adapters/`: CSV reader, database connection manager
  - `config/`: Database connection strings, schema management
  - `migrations/`: Alembic-based schema versioning
  - **Depends on Core** via interface implementations

#### **Layer 3: Application (Orchestration)**
- **Location**: `src/application/`
- **Responsibility**: Workflow orchestration, error handling, reporting
- **Contents**:
  - `import_service.py`: Main import coordinator
  - `error_handler.py`: Centralized error and validation failure handling
  - `progress_tracker.py`: Audit trail and import statistics
  - **Depends on Core and Infrastructure**

#### **Layer 4: Presentation (CLI/API)**
- **Location**: `src/cli/`
- **Responsibility**: User interface, argument parsing, logging
- **Contents**:
  - `main.py`: Entry point and CLI argument parsing
  - `output_formatter.py`: Console output and reporting
  - **Depends on Application layer**

### 3.2 Project Structure

```
src/
├── core/
│   ├── __init__.py
│   ├── entities/
│   │   ├── person.py
│   │   ├── program.py
│   │   ├── enrollment.py
│   │   ├── reference_data.py
│   │   └── ...
│   ├── use_cases/
│   │   ├── import_reference_data.py
│   │   ├── import_persons.py
│   │   ├── import_programs.py
│   │   ├── validate_referential_integrity.py
│   │   └── ...
│   └── ports/
│       ├── repository.py
│       ├── validator.py
│       └── progress_reporter.py
├── infrastructure/
│   ├── __init__.py
│   ├── adapters/
│   │   ├── csv_reader.py
│   │   └── postgres_connector.py
│   ├── repositories/
│   │   ├── base_repository.py
│   │   ├── person_repository.py
│   │   ├── program_repository.py
│   │   └── ...
│   ├── config/
│   │   ├── database.py
│   │   └── settings.py
│   └── migrations/
│       └── versions/
├── application/
│   ├── __init__.py
│   ├── import_service.py
│   ├── error_handler.py
│   ├── validation_service.py
│   └── progress_tracker.py
├── cli/
│   ├── __init__.py
│   ├── main.py
│   └── output_formatter.py
└── __init__.py

tests/
├── unit/
│   ├── test_entities.py
│   ├── test_use_cases.py
│   └── test_validators.py
├── integration/
│   ├── test_csv_parsing.py
│   ├── test_database_operations.py
│   └── test_import_workflow.py
└── fixtures/
    └── sample_data.py

config/
├── database.ini
├── alembic.ini
└── logging.yaml

docs/
├── GUIDE_SCHEMA_NOTES.md
├── CSV_MAPPING.md
└── TROUBLESHOOTING.md

pyproject.toml
requirements.txt
```

---

## 4. Detailed Design

### 4.1 Data Import Workflow

```
┌─────────────────────────────────────────────────┐
│ 1. Bootstrap & Configuration                    │
│    - Load database config                       │
│    - Verify PostgreSQL connectivity             │
│    - Initialize Alembic migrations              │
└────────────────┬────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────┐
│ 2. Schema Initialization                        │
│    - Apply Alembic migrations (create tables)   │
│    - Set up constraints and indexes             │
└────────────────┬────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────┐
│ 3. Load Reference Data (Priority 1)             │
│    - ReferenceCodeSet, ReferenceCodeValue       │
│    - All *Lookup tables (sorted by dependency)  │
│    - Validation: Check for completeness        │
└────────────────┬────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────┐
│ 4. Load Core Entities (Priority 2)              │
│    - Tenant, Organization, Site                 │
│    - PersonLookup, PersonDemographics           │
│    - ProgramOfStudyLookup, AcademicCatalog      │
│    - Validation: PK uniqueness, data quality    │
└────────────────┬────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────┐
│ 5. Load Relationships (Priority 3)              │
│    - PersonProgram, Enrollment, Cohort          │
│    - CourseTermAssociation                      │
│    - Validation: FK constraints, cardinality    │
└────────────────┬────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────┐
│ 6. Load Advisor-Specific Data (Priority 4)      │
│    - PersonProgramProgressEvaluation            │
│    - LearnerDegreePlan & items                  │
│    - PersonSupportAssignment & referrals        │
│    - LearnerEarlyAlert, predictions             │
│    - Validation: Progress consistency           │
└────────────────┬────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────┐
│ 7. Post-Load Validation                         │
│    - Check referential integrity                │
│    - Identify orphaned records                  │
│    - Verify data quality flags                  │
│    - Generate import report                     │
└────────────────┬────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────┐
│ 8. Finalization                                 │
│    - Create audit trail record                  │
│    - Log success/failure statistics             │
│    - Return exit code and summary               │
└─────────────────────────────────────────────────┘
```

### 4.2 Command/Query Objects (CQRS Pattern)

Following clean architecture principles, all use cases accept command or query objects:

```python
# Commands (state-modifying operations)
class ImportReferenceDataCommand:
    csv_directory: str
    reference_tables: List[str]
    skip_if_exists: bool = False

class ImportPersonDataCommand:
    csv_file: str
    tenant_id: str
    validate_only: bool = False

# Queries (read-only operations)
class GetImportStatisticsQuery:
    tenant_id: str
    include_validation_errors: bool = True

class GetDataQualityReportQuery:
    tenant_id: str
    threshold_percentage: float = 95.0
```

### 4.3 Result Objects

All use cases return standardized result objects:

```python
class ImportResult:
    success: bool
    records_processed: int
    records_failed: int
    warnings: List[str]
    errors: List[ValidationError]
    duration_seconds: float
    audit_trail_id: str  # Link to import audit record
```

### 4.4 Core Domain Entities

**Example: Person Entity**
```python
# src/core/entities/person.py
class Person:
    tenant_id: str
    person_id: str
    first_name: str
    last_name: str
    birth_date: Optional[date]
    birth_date_quality: DataQuality
    source_system_id: str
    source_system_key_value: str
    record_start_date: Optional[date]
    record_end_date: Optional[date]
    status: str
    created_by: str
    created_date: datetime
    updated_by: str
    updated_date: datetime
    
    def is_active(self, as_of_date: date) -> bool:
        """Temporal query for advisor workflows"""
```

### 4.5 Validation Strategy

**Multi-level validation:**

1. **Structural Validation** (CSV parsing layer)
   - Column presence and order
   - Type coercion (strings → dates, UUIDs, etc.)
   - Null handling per GUIDE schema

2. **Semantic Validation** (Domain layer)
   - Business rule enforcement (e.g., `RecordEndDate > RecordStartDate`)
   - Required field presence
   - Format validation (e.g., UUID format, date ranges)

3. **Referential Validation** (Post-load)
   - Foreign key resolution
   - Orphaned record detection
   - Circular dependency checks

4. **Data Quality Validation**
   - Quality flag interpretation (e.g., "Full SSN reported")
   - Cardinality checks (1:1, 1:N relationships)
   - Temporal consistency (no time-travel)

---

## 5. Technology Stack

### Core Dependencies

```
Python == 3.11+
PostgreSQL == 15+
sqlalchemy == 2.0+        # ORM for data access
alembic == 1.13+          # Database schema migrations
pandas == 2.1+            # CSV parsing (efficient for 116 files)
pydantic == 2.0+          # Data validation and serialization
psycopg2-binary == 2.9+   # PostgreSQL adapter
python-dotenv == 1.0+     # Environment configuration
click == 8.1+             # CLI framework
tenacity == 8.2+          # Retry logic for robustness
```

### Development & Testing

```
pytest == 7.4+
pytest-cov == 4.1+
pytest-mock == 3.12+
black == 23.11+           # Code formatting
flake8 == 6.1+            # Linting
mypy == 1.7+              # Type checking
```

---

## 6. Implementation Phases

### Phase 1: Foundation (Weeks 1-2)
- [x] Repository structure and CI/CD setup
- [x] Database schema (Alembic migrations)
- [x] Base repository and entity classes
- [x] CSV reader adapter
- [ ] Unit tests for core entities

### Phase 2: Reference Data & Core Entities (Weeks 3-4)
- [ ] Import use cases for ReferenceCodeSet, ReferenceCodeValue
- [ ] Import use cases for all lookup tables (with dependency ordering)
- [ ] Import use cases for Person, Program, Organization
- [ ] Integration tests for Phase 2 workflows

### Phase 3: Relationships & Validation (Weeks 5-6)
- [ ] Import use cases for Enrollment, PersonProgram, Cohort
- [ ] Referential integrity validation service
- [ ] Data quality reporting
- [ ] Error recovery and retry logic

### Phase 4: Advisor-Specific Data (Weeks 7-8)
- [ ] Import use cases for LearnerDegreePlan, PersonSupportAssignment
- [ ] Progress evaluation validation
- [ ] Early alert and prediction loading
- [ ] Advisor-facing data quality checks

### Phase 5: CLI & Documentation (Week 9)
- [ ] Click-based CLI with progress reporting
- [ ] Comprehensive logging and audit trails
- [ ] End-to-end test suite
- [ ] User and operator documentation

---

## 7. Data Mapping & ETL Rules

### 7.1 CSV to PostgreSQL Column Mapping

**Principles:**
- Preserve source column names as-is in the data warehouse
- Add computed/derived columns as needed for advisor workflows
- Maintain data quality metadata from source

**Example Mapping (PersonLookup):**

| CSV Column | PostgreSQL Column | Type | Nullable | Notes |
|---|---|---|---|---|
| TenantIdentifier | tenant_id | UUID | NO | Partition key |
| PersonIdentifier | person_id | VARCHAR(50) | NO | Business key (source) |
| FirstName | first_name | VARCHAR(255) | YES | |
| BirthDate | birth_date | DATE | YES | Check validity |
| BirthDateQuality | birth_date_quality | VARCHAR(100) | YES | {Full DOB, Partial, Client prefers not to answer, ...} |
| SourceSystemIdentifier | source_system_id | VARCHAR(50) | NO | Lineage tracking |
| SourceSystemKeyValue | source_system_key_value | VARCHAR(255) | NO | External system PK |
| RecordStartDate | record_start_date | DATE | YES | Temporal validity |
| RecordEndDate | record_end_date | DATE | YES | Temporal validity |
| CreatedDate | created_at | TIMESTAMP | NO | Audit |
| UpdatedDate | updated_at | TIMESTAMP | NO | Audit |

### 7.2 Dependency Ordering

**Load order for lookup tables:**

1. `ReferenceCodeSet` (parent of all lookups)
2. `ReferenceCodeValue` (values for code sets)
3. All other lookups in topological order:
   - First: Independent lookups (RoleLookup, EmailTypeLookup, etc.)
   - Then: Lookups with FK to ReferenceCodeSet (CourseStatusLookup, etc.)
   - Then: Hierarchical lookups (OrganizationUnitTypeLookup, etc.)

**Load order for entities:**

1. Tenant (all entities reference Tenant)
2. Organization, Site (foundational)
3. Person, PersonDemographics (core person data)
4. Program, ProgramRequirement, ProgramRequirementCourse
5. Enrollment, PersonProgram, Cohort
6. LearnerDegreePlan, LearnerDegreePlanItem
7. PersonSupportAssignment, PersonSupportReferral
8. LearnerEarlyAlert, LearnerSuccessPrediction

---

## 8. Error Handling & Recovery

### 8.1 Recoverable Errors

- **Duplicate key** → Skip with warning
- **Data type mismatch** → Attempt coercion; log if fails
- **NULL violation on optional field** → Set to NULL or default
- **FK constraint violation** → Log as warning; allow continuation (for orphaned records)

### 8.2 Fatal Errors

- **File not found** → Stop
- **Database connection failure** → Stop with error
- **Schema mismatch** → Stop; suggest Alembic migration
- **Data integrity after validation** → Rollback transaction

### 8.3 Retry Strategy

Using `tenacity` library:
- Max retries: 3
- Backoff: exponential (1s, 2s, 4s)
- Retry on: `OperationalError`, `DatabaseError`, temporary connection issues

---

## 9. Performance Considerations

### 9.1 Bulk Loading

- Use PostgreSQL `COPY` command for large tables (> 10K rows)
- Batch inserts in transactions (1000-5000 rows per batch)
- Parallel loading where dependencies allow

### 9.2 Indexing

- Create indexes after bulk load (faster insertion)
- Indexes on foreign keys, commonly queried columns
- Composite indexes for advisor queries (e.g., person_id + term)

### 9.3 Monitoring

- Log rows processed per minute
- Track memory usage (important with pandas)
- Report elapsed time per entity type

---

## 10. Testing Strategy

### 10.1 Unit Tests

- Entity creation and validation
- Use case command/query processing
- Validator rule enforcement
- ~70% coverage target

### 10.2 Integration Tests

- CSV parsing with real sample data
- Database operations (insert, update, query)
- Foreign key constraint enforcement
- End-to-end import workflow (subset of data)
- ~80% coverage target

### 10.3 Test Fixtures

- Sample CSV files with known record counts
- Sample database states for validation testing
- Common error scenarios (malformed dates, missing FKs, etc.)

---

## 11. Monitoring & Auditing

### 11.1 Import Audit Trail

**Table: import_audit_trail**

| Column | Type | Purpose |
|---|---|---|
| import_id | UUID | Unique import run |
| started_at | TIMESTAMP | Start time |
| completed_at | TIMESTAMP | End time |
| status | ENUM (success, partial, failed) | Overall result |
| tenant_id | UUID | Target tenant |
| total_records | INT | Records processed |
| failed_records | INT | Errors encountered |
| validation_errors | JSONB | Detailed errors |
| created_by | VARCHAR | Import operator |

### 11.2 Logging

- **Level INFO**: Import phase start/end, record counts
- **Level WARNING**: Recoverable errors, data quality issues
- **Level ERROR**: Fatal errors, validation failures
- **Format**: JSON for structured logging (integration with ELK, Datadog, etc.)

---

## 12. Security & Compliance

- **Secrets management**: Use `.env` and environment variables (no hardcoded credentials)
- **Audit trails**: Preserve `CreatedBy`, `UpdatedBy` for compliance
- **Data sensitivity**: Mask PII in logs (SSN, DOB, etc.)
- **Tenant isolation**: Enforce tenant_id filtering at all levels
- **Access control**: Import operation restricted to authenticated operators

---

## 13. Documentation Requirements

1. **CSV_MAPPING.md**: Detailed column-by-column mapping
2. **GUIDE_SCHEMA_NOTES.md**: Entity relationships and cardinality
3. **TROUBLESHOOTING.md**: Common errors and recovery steps
4. **OPERATOR_GUIDE.md**: How to run the import and interpret results
5. **API_DOCS.md**: Use case interfaces and result objects

---

## 14. Success Criteria

- ✓ All 116 CSV files successfully loaded
- ✓ Referential integrity maintained (0 orphaned records)
- ✓ Data quality report generated and reviewed
- ✓ Advisor queries (degree plan, progress, support) return correct results
- ✓ Import completes in < 10 minutes for full dataset
- ✓ 80%+ test coverage
- ✓ No PII exposed in logs or error messages
- ✓ Operator documentation complete and tested

---

## 15. Future Enhancements

1. **Incremental updates**: Support daily/weekly data refreshes
2. **Data reconciliation**: Detect and flag inconsistencies between source and warehouse
3. **Retention policies**: Purge old import audit trails
4. **Performance tuning**: Parallel entity loading, materialized views for advisor queries
5. **GraphQL API**: Direct advisor tool access to imported data
6. **Data quality dashboard**: Real-time monitoring of data completeness/accuracy

---

## Appendix A: Dependency Graph (Lookup Tables)

```
ReferenceCodeSet (root)
    └── ReferenceCodeValue
        ├── CourseStatusLookup
        ├── EnrollmentStatusLookup
        ├── GradeDefinitionLookup
        ├── ApplicationStatusLookup
        ├── ... (all other status lookups)
        └── RoleLookup

ApplicationDecisionTypeLookup (independent)
ApplicationSourceLookup (independent)
AddressTypeLookup (independent)
EmailTypeLookup (independent)
... (16 other independent lookups)

OrganizationUnitTypeLookup (independent)
```

---

## Appendix B: CSV File Inventory

**Total Files:** 116

**Categories:**
- **Reference Data (27):** Lookup tables for codes, types, statuses
- **Person Data (11):** Demographics, contact info, employment, housing
- **Academic Data (23):** Catalog, curriculum, requirements, assessment
- **Enrollment Data (15):** Enrollments, attendance, credits, outcomes
- **Support & Advisement (12):** Support assignments, referrals, alerts, predictions
- **Career & Transfer (7):** Career pathways, transfer evaluations
- **Administrative (11):** Tenants, organizations, sites, terms, roles

---

**Document Owner:** Data Engineering Team  
**Last Updated:** 2026-11-08  
**Next Review:** 2026-11-22
