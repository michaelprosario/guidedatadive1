# GUIDE Data Import Program - Architecture Diagram

## System Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                      CSV Data Sources (116 files)                │
│  ┌──────────────────────────────────────────────────────────────┐│
│  │ Reference Data        Core Entities      Relationships        ││
│  │ • ReferenceCodeSet   • PersonLookup     • Enrollment         ││
│  │ • LookupTables (27)   • Organization    • Cohort             ││
│  │                       • Program          • PersonProgram      ││
│  │                                          • CourseTermAssoc    ││
│  │                      Advisor Data                            ││
│  │                      • LearnerDegreePlan                     ││
│  │                      • PersonSupport*                        ││
│  │                      • LearnerEarlyAlert                     ││
│  └──────────────────────────────────────────────────────────────┘│
└────────────┬─────────────────────────────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────────────────────────────┐
│                  CLI Layer (src/cli/)                             │
│  ┌──────────────────────────────────────────────────────────────┐│
│  │ main.py (Click)  │  output_formatter.py                     ││
│  │  • --csv-dir     │  • Console output                         ││
│  │  • --db-url      │  • Progress reporting                     ││
│  │  • --dry-run     │  • Error summaries                        ││
│  │  • --tenant-id   │  • Audit trail output                     ││
│  └──────────────────────────────────────────────────────────────┘│
└────────────┬─────────────────────────────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────────────────────────────┐
│               Application Layer (src/application/)               │
│  ┌──────────────────────────────────────────────────────────────┐│
│  │                     ImportService                            ││
│  │  ┌─────────────────────────────────────────────────────────┐ ││
│  │  │  run_import()                                           │ ││
│  │  │  ├─ Phase 1: Bootstrap & Schema Init                  │ ││
│  │  │  ├─ Phase 2: Load Reference Data                      │ ││
│  │  │  ├─ Phase 3: Load Core Entities                       │ ││
│  │  │  ├─ Phase 4: Load Relationships                       │ ││
│  │  │  ├─ Phase 5: Load Advisor-Specific Data               │ ││
│  │  │  ├─ Phase 6: Post-Load Validation                     │ ││
│  │  │  └─ Phase 7: Finalization & Audit Trail              │ ││
│  │  └─────────────────────────────────────────────────────────┘ ││
│  │                                                              ││
│  │  ┌────────────────────────┐  ┌────────────────────────────┐││
│  │  │ ErrorHandler           │  │ ProgressTracker            │││
│  │  │ • Recoverable errors   │  │ • Records processed        │││
│  │  │ • Fatal errors         │  │ • Failures tracked         │││
│  │  │ • Retry logic          │  │ • Import audit trail       │││
│  │  │ • Rollback on failure  │  │ • Statistics reported      │││
│  │  └────────────────────────┘  └────────────────────────────┘││
│  │                                                              ││
│  │  ┌─────────────────────────────────────────────────────────┐││
│  │  │ ValidationService                                       │││
│  │  │ • Structural validation (CSV parsing)                   │││
│  │  │ • Semantic validation (business rules)                  │││
│  │  │ • Referential validation (FK checks)                    │││
│  │  │ • Data quality validation (quality flags)               │││
│  │  └─────────────────────────────────────────────────────────┘││
│  └──────────────────────────────────────────────────────────────┘│
└────────────┬─────────────────────────────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────────────────────────────┐
│                  Core Layer (src/core/)                           │
│                 [Zero Framework Dependencies]                     │
│  ┌──────────────────────────────────────────────────────────────┐│
│  │                    USE CASES                                 ││
│  │  ┌───────────────────┐  ┌──────────────────┐                ││
│  │  │ ImportReference   │  │ ImportPersons    │                ││
│  │  │ DataUseCase       │  │ UseCase          │                ││
│  │  └───────────────────┘  └──────────────────┘                ││
│  │  ┌───────────────────┐  ┌──────────────────┐                ││
│  │  │ ImportPrograms    │  │ ImportEnrollment │                ││
│  │  │ UseCase           │  │ UseCase          │                ││
│  │  └───────────────────┘  └──────────────────┘                ││
│  │  ┌───────────────────┐  ┌──────────────────┐                ││
│  │  │ ValidateReferential│ │ LoadAdvisor      │                ││
│  │  │ IntegrityUseCase  │  │ DataUseCase      │                ││
│  │  └───────────────────┘  └──────────────────┘                ││
│  │                                                              ││
│  │  Input: Command Objects (CQRS)                              ││
│  │  Output: Result Objects                                     ││
│  │                                                              ││
│  │  ┌───────────────────────────────────────────────────────┐ ││
│  │  │ All use cases communicate via interfaces (Ports)      │ ││
│  │  │ • IRepository interface                               │ ││
│  │  │ • IValidator interface                                │ ││
│  │  │ • IProgressReporter interface                         │ ││
│  │  └───────────────────────────────────────────────────────┘ ││
│  │                                                              ││
│  │                    ENTITIES                                 ││
│  │  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐   ││
│  │  │ Person       │  │ Program      │  │ Enrollment      │   ││
│  │  │ • person_id  │  │ • program_id │  │ • enrollment_id │   ││
│  │  │ • first_name │  │ • title      │  │ • student_id    │   ││
│  │  │ • status     │  │ • credits    │  │ • term_id       │   ││
│  │  │ • audit meta │  │ • audit meta │  │ • audit meta    │   ││
│  │  └──────────────┘  └──────────────┘  └─────────────────┘   ││
│  │  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐   ││
│  │  │ DegreePlan   │  │ Support      │  │ LearnerAlertice │   ││
│  │  │ • plan_id    │  │ • support_id │  │ • alert_id      │   ││
│  │  │ • student_id │  │ • person_id  │  │ • student_id    │   ││
│  │  │ • status     │  │ • role_id    │  │ • trigger       │   ││
│  │  │ • audit meta │  │ • audit meta │  │ • audit meta    │   ││
│  │  └──────────────┘  └──────────────┘  └─────────────────┘   ││
│  └──────────────────────────────────────────────────────────────┘│
└────────────┬─────────────────────────────────────────────────────┘
             │ implements
             ▼
┌──────────────────────────────────────────────────────────────────┐
│             Infrastructure Layer (src/infrastructure/)            │
│                 [Framework & Technical Details]                   │
│  ┌──────────────────────────────────────────────────────────────┐│
│  │                  ADAPTERS                                    ││
│  │  ┌────────────────────────┐  ┌──────────────────────────┐   ││
│  │  │ CSVReader              │  │ PostgresConnector        │   ││
│  │  │ • read_file()          │  │ • connect()              │   ││
│  │  │ • read_directory()     │  │ • create_engine()        │   ││
│  │  │ • type_coercion()      │  │ • execute_sql()          │   ││
│  │  │ • null_handling()      │  │ • begin_transaction()    │   ││
│  │  └────────────────────────┘  └──────────────────────────┘   ││
│  │                                                              ││
│  │                 REPOSITORIES                                 ││
│  │  (Implement IRepository interface)                           ││
│  │  ┌───────────────────────────────────────────────────────┐  ││
│  │  │ • PersonRepository        • ProgramRepository        │  ││
│  │  │ • EnrollmentRepository     • DegreePlanRepository    │  ││
│  │  │ • ReferenceDataRepository  • SupportRepository       │  ││
│  │  │ • CourseRepository         • AlertRepository         │  ││
│  │  │ Each implements:                                     │  ││
│  │  │ • add(entity) → void                                 │  ││
│  │  │ • get_by_id(id) → entity                             │  ││
│  │  │ • get_all() → List[entity]                           │  ││
│  │  │ • bulk_insert(entities) → void                       │  ││
│  │  │ • validate_foreign_keys() → List[errors]             │  ││
│  │  └───────────────────────────────────────────────────────┘  ││
│  │                                                              ││
│  │                CONFIGURATION                                ││
│  │  ┌─────────────────────────┐                              ││
│  │  │ database.py             │                              ││
│  │  │ • DB_URL                │                              ││
│  │  │ • connection pool setup │                              ││
│  │  │ • timeout config        │                              ││
│  │  └─────────────────────────┘                              ││
│  │                                                              ││
│  │                MIGRATIONS (Alembic)                          ││
│  │  ┌───────────────────────────────────────────────────────┐  ││
│  │  │ migrations/versions/                                  │  ││
│  │  │ • 001_create_reference_tables.py                      │  ││
│  │  │ • 002_create_person_tables.py                         │  ││
│  │  │ • 003_create_enrollment_tables.py                     │  ││
│  │  │ • 004_create_advisor_tables.py                        │  ││
│  │  │ • 005_create_indexes.py                               │  ││
│  │  │ • 006_create_audit_trail_table.py                     │  ││
│  │  └───────────────────────────────────────────────────────┘  ││
│  └──────────────────────────────────────────────────────────────┘│
└────────────┬─────────────────────────────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────────────────────────────┐
│              PostgreSQL Database (15+)                            │
│  ┌──────────────────────────────────────────────────────────────┐│
│  │ Schema: guide_public                                         ││
│  │                                                              ││
│  │ Reference Tables         │  Core Entity Tables             ││
│  │ ├─ reference_code_set    │  ├─ person_lookup              ││
│  │ ├─ reference_code_value  │  ├─ organization               ││
│  │ ├─ course_status_lookup  │  ├─ program_of_study           ││
│  │ ├─ enrollment_status_... │  ├─ academic_catalog           ││
│  │ └─ [25 more lookups]     │  ├─ person_program             ││
│  │                          │  ├─ course_lookup              ││
│  │ Advisor Tables           │  ├─ enrollment                 ││
│  │ ├─ learner_degree_plan   │  ├─ cohort                     ││
│  │ ├─ learner_deg_plan_item │  └─ person_support_...         ││
│  │ ├─ person_support_assign │                                ││
│  │ ├─ learner_early_alert   │  Audit & Tracking             ││
│  │ ├─ learner_success_pred  │  ├─ import_audit_trail        ││
│  │ └─ career_pathway        │  └─ data_quality_report       ││
│  │                          │                                ││
│  │ Indexes: On all PKs, FKs, commonly queried columns       ││
│  │ Constraints: Referential integrity, NOT NULL where req'd  ││
│  └──────────────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────────┘
```

---

## Dependency Flow (Inversion of Control)

```
                    Core Layer
                   (Business Logic)
                        ▲
                        │
                  ┌─────┴─────┐
                  │           │
             depends on   depends on
                  │           │
                  ▼           ▼
            IRepository  IValidator
             (Interface)  (Interface)
                  ▲           ▲
                  │ implements │ implements
                  │           │
    ┌─────────────┴───┬───────┴──────────┐
    │                 │                  │
Infrastructure Layer  ─
PersonRepository  ValidationService  ErrorHandler
   ▲                  ▲                  ▲
└──────────────────────────────────────────┘

Key Principle: Core depends on Interfaces, 
              Infrastructure implements Interfaces
              ➜ Core is framework-independent
              ➜ Easy to test (mock implementations)
              ➜ Easy to swap implementations
```

---

## Data Flow: Import Example

```
CSV File (PersonLookup.csv)
    │
    ├─[CSVReader.read_file()]─► DataFrame
    │
    ├─[Structural Validation]
    │  • Check columns exist
    │  • Type coercion (str → date)
    │  • NULL handling
    │
    ├─[Semantic Validation]
    │  • Person entity rules
    │  • Date logic (end_date > start_date)
    │  • Required fields
    │
    ├─[ImportPersonsUseCase.execute()] ─ Command/Query Pattern
    │  Input:  ImportPersonsCommand(csv_file, tenant_id)
    │  Output: ImportResult(success, count, errors)
    │
    ├─[PersonRepository.bulk_insert()]
    │  • Batch by 1000 rows
    │  • Transaction per batch
    │  • Catch IntegrityError (duplicates)
    │
    └──► PostgreSQL Database (person_lookup table)
         │
         ├─ Referential Validation (post-load)
         │  • Check all FKs exist
         │  • Identify orphaned records
         │
         └─► import_audit_trail table (success record)
             • import_id, started_at, completed_at
             • status, records_processed, errors
```

---

## Testing Architecture

```
┌─────────────────────────────────────────┐
│        tests/                           │
│  ┌─────────────────────────────────────┐│
│  │ unit/                               ││
│  │ • test_entities.py                  ││
│  │   - Entity creation                 ││
│  │   - Validation rules                ││
│  │   - Business logic                  ││
│  │                                     ││
│  │ • test_use_cases.py                 ││
│  │   - Use case execution              ││
│  │   - Command/Query handling          ││
│  │   - Error conditions                ││
│  │                                     ││
│  │ • test_validators.py                ││
│  │   - Structural validation           ││
│  │   - Semantic validation             ││
│  │   - Quality checks                  ││
│  └─────────────────────────────────────┘│
│  ┌─────────────────────────────────────┐│
│  │ integration/                        ││
│  │ • test_csv_parsing.py               ││
│  │   - Real CSV files                  ││
│  │   - Encoding issues                 ││
│  │                                     ││
│  │ • test_database_operations.py       ││
│  │   - Repository CRUD                 ││
│  │   - FK constraints                  ││
│  │   - Transaction handling            ││
│  │                                     ││
│  │ • test_import_workflow.py           ││
│  │   - Full import phases              ││
│  │   - Error recovery                  ││
│  │   - Advisor queries                 ││
│  └─────────────────────────────────────┘│
│  ┌─────────────────────────────────────┐│
│  │ fixtures/                           ││
│  │ • sample_data.py                    ││
│  │   - Test entities                   ││
│  │   - Sample DataFrames               ││
│  │   - Mock objects                    ││
│  │                                     ││
│  │ • test_csvs/                        ││
│  │   - Mini versions of each CSV       ││
│  │   - Known good records              ││
│  │   - Error scenarios                 ││
│  └─────────────────────────────────────┘│
└─────────────────────────────────────────┘
```

---

## Deployment Architecture

```
Developer Machine
    ├─ Python 3.11 + venv
    ├─ PostgreSQL 15 (local Docker)
    └─ Git repository
         │
         ├─ src/ (application code)
         ├─ tests/ (test suite)
         ├─ config/ (configuration)
         │
         ├─ pyproject.toml (dependencies)
         └─ .env (secrets, not committed)

                    │
                    ▼ (git push)

GitHub Repository
    ├─ main branch (stable releases)
    ├─ develop branch (integration)
    └─ feature branches (in-progress work)

                    │
                    ▼ (CI/CD Pipeline - Future)

Production Environment
    ├─ PostgreSQL 15 (managed database)
    ├─ Application server (Python ASGI)
    ├─ Load balancer (optional)
    └─ Monitoring/Logging (Datadog/ELK)
```

---

## Scaling Considerations

```
Single Dataset Import (Current)
├─ Sequential loading by phase
├─ Single connection pool
├─ ~10 minutes for 116 CSV files
└─ 50-100 MB memory peak

Multi-Tenant Scaling (Future)
├─ Parallel imports (different tenants)
├─ Connection pool per tenant
├─ Multiple workers
└─ Higher memory/CPU requirements

Real-Time Integration (Future)
├─ Event streaming (Kafka)
├─ Change data capture (CDC)
├─ Incremental updates
└─ Real-time advisor dashboard
```

---

**For implementation details, see [IMPLEMENTATION_GUIDE.md](/workspaces/guidedatadive1/IMPLEMENTATION_GUIDE.md)**

**For design rationale, see [techSpec1.md](/workspaces/guidedatadive1/techSpec1.md)**
