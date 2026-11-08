# GUIDE Data Import Program - Implementation Checklist

Use this checklist to track progress as you implement the import program outlined in the technical specifications.

**Estimated Duration:** 9 weeks (Phase 1-5)  
**Start Date:** [To be determined]  
**Target Completion:** [To be determined]  

---

## Phase 1: Foundation (Weeks 1-2)

**Objective:** Set up project infrastructure, base classes, and CSV adapter

### Setup & Configuration
- [ ] Create GitHub repository with branch protection
- [ ] Set up `.gitignore` (Python, virtual environments, secrets)
- [ ] Create `requirements.txt` with all dependencies
- [ ] Set up Python virtual environment locally
- [ ] Create `.env.example` file (no secrets)
- [ ] Configure Git hooks (pre-commit linting, tests)
- [ ] Set up GitHub Actions CI/CD pipeline

### Project Structure
- [ ] Create `src/` directory structure (all 8 subdirectories)
- [ ] Create `tests/` directory structure (unit, integration, fixtures)
- [ ] Create `config/` directory (database.ini, alembic.ini, logging.yaml)
- [ ] Create `docs/` directory for documentation files
- [ ] Add `__init__.py` to all package directories

### Database Setup
- [ ] Install PostgreSQL 15+ locally (or connect to managed instance)
- [ ] Create database `guide_db` and schema `guide_public`
- [ ] Create `.env` file with `DATABASE_URL`
- [ ] Test database connectivity from Python

### Alembic Migrations
- [ ] Initialize Alembic: `alembic init alembic`
- [ ] Configure `alembic.ini` with database URL
- [ ] Create first migration version (empty): `001_initial.py`
- [ ] Test migration: `alembic upgrade head`

### Core Domain Layer
- [ ] Create `src/core/entities/__init__.py` with base Entity class
  - [ ] Implement `@dataclass` decorator pattern
  - [ ] Add common audit fields (created_date, updated_date, created_by)
  - [ ] Add validation method stub
- [ ] Create `src/core/ports/repository.py`
  - [ ] Define `IRepository[T]` interface
  - [ ] Specify generic CRUD methods: `add()`, `get_by_id()`, `get_all()`
  - [ ] Add bulk operations: `bulk_insert()`, `delete_by_id()`
- [ ] Create `src/core/ports/validator.py`
  - [ ] Define `IValidator` interface
  - [ ] Specify validation methods
- [ ] Create `src/core/ports/progress_reporter.py`
  - [ ] Define `IProgressReporter` interface
  - [ ] Report phase start/end, row counts

### Infrastructure Adapters
- [ ] Create `src/infrastructure/adapters/csv_reader.py`
  - [ ] Implement `read_file(path)` → DataFrame
  - [ ] Implement `read_directory(dir, pattern)` → Iterator
  - [ ] Handle CSV encoding issues (UTF-8, BOM)
  - [ ] Test with sample PersonLookup.csv file
- [ ] Create `src/infrastructure/adapters/postgres_connector.py`
  - [ ] Create SQLAlchemy engine
  - [ ] Implement connection pool
  - [ ] Add connection testing
  - [ ] Handle connection errors gracefully

### First Entity & Repository
- [ ] Create `src/core/entities/reference_data.py`
  - [ ] Implement `ReferenceCodeSet` entity (minimal)
  - [ ] Implement `ReferenceCodeValue` entity (minimal)
- [ ] Create `src/infrastructure/repositories/base_repository.py`
  - [ ] Implement generic base class for all repositories
  - [ ] Transaction management
  - [ ] Error handling
- [ ] Create `src/infrastructure/repositories/reference_data_repository.py`
  - [ ] Implement `IRepository` for ReferenceCodeSet
  - [ ] SQLAlchemy ORM models
  - [ ] Basic CRUD operations
  - [ ] Bulk insert optimized for large datasets

### Testing Framework
- [ ] Configure `pytest.ini` (test discovery, markers)
- [ ] Create `tests/conftest.py` (shared fixtures)
- [ ] Create `tests/fixtures/sample_data.py`
  - [ ] Sample ReferenceCodeSet entities
  - [ ] Sample DataFrames for testing
- [ ] Create `tests/unit/test_entities.py`
  - [ ] Test entity creation
  - [ ] Test entity validation
  - [ ] Test default values
- [ ] Set up pytest-cov for coverage reporting
- [ ] Create GitHub Actions workflow to run tests on commit

### Documentation
- [ ] Create `IMPLEMENTATION_GUIDE.md` (started)
- [ ] Create `techSpec1.md` (started)
- [ ] Create `docs/TESTING.md` (how to run tests)
- [ ] Create `docs/SETUP.md` (environment setup)
- [ ] Add README.md with project overview

### Validation
- [ ] Run all unit tests: `pytest tests/unit/`
- [ ] Check coverage: `pytest --cov=src`
- [ ] Lint code: `flake8 src/`
- [ ] Type check: `mypy src/`
- [ ] Verify database connectivity

**Completion Sign-off:**
- [ ] All checklist items complete
- [ ] Code review passed
- [ ] Tests passing (80%+ would be Phase 2+)
- [ ] Documentation reviewed

---

## Phase 2: Reference Data & Core Entities (Weeks 3-4)

**Objective:** Load lookup tables and core person/program data

### Database Schema (Alembic Migrations)
- [ ] Create migration: `002_create_lookup_tables.py`
  - [ ] Tables: ReferenceCodeSet, ReferenceCodeValue
  - [ ] Add indexes on PKs and commonly queried columns
  - [ ] Add NOT NULL constraints
  - [ ] Test migration: `alembic upgrade head`
- [ ] Create migration: `003_create_person_tables.py`
  - [ ] Tables: Person, PersonDemographics, PersonPhone, PersonEmail, PersonAddress
  - [ ] Foreign keys to Tenant, Organization
  - [ ] Audit fields
  - [ ] Test migration
- [ ] Create migration: `004_create_program_tables.py`
  - [ ] Tables: ProgramOfStudyLookup, AcademicCatalog, ProgramRequirement, ProgramRequirementCourse
  - [ ] Test migration

### Lookup Table Entities
- [ ] Create `src/core/entities/lookup.py`
  - [ ] All 27 lookup entity classes (e.g., RoleL, CourseStatusL)
  - [ ] Each with required fields and audit metadata
  - [ ] Validation methods for each
- [ ] Create dependency ordering logic in `src/core/use_cases/lookup_dependency_sorter.py`
  - [ ] Topological sort of lookup tables
  - [ ] Document dependency graph (in docs/)

### Core Entity Models
- [ ] Create `src/core/entities/person.py`
  - [ ] Person, PersonDemographics, PersonPhone, PersonEmail, PersonAddress
- [ ] Create `src/core/entities/program.py`
  - [ ] ProgramOfStudyLookup, AcademicCatalog, ProgramRequirement, ProgramRequirementCourse
- [ ] Create `src/core/entities/organization.py`
  - [ ] Tenant, Organization, Site

### Repository Implementations
- [ ] Create `src/infrastructure/repositories/lookup_repository.py`
  - [ ] Generic implementation for all lookup tables
  - [ ] Bulk insert optimized
- [ ] Create `src/infrastructure/repositories/person_repository.py`
  - [ ] CRUD for Person, PersonDemographics, etc.
  - [ ] Query by tenant_id
  - [ ] Check for duplicates
- [ ] Create `src/infrastructure/repositories/program_repository.py`
  - [ ] CRUD for program entities
  - [ ] Query by tenant and academic period

### Use Cases
- [ ] Create `src/core/use_cases/import_reference_data.py`
  - [ ] `ImportReferenceDataCommand` class
  - [ ] `ImportReferenceDataUseCase` execution logic
  - [ ] Dependency ordering
  - [ ] Error handling (duplicate keys, etc.)
  - [ ] Return `ImportResult` with statistics
- [ ] Create `src/core/use_cases/import_person_data.py`
  - [ ] `ImportPersonDataCommand` class
  - [ ] `ImportPersonDataUseCase` execution logic
  - [ ] Validate data quality flags
  - [ ] Return `ImportResult`
- [ ] Create `src/core/use_cases/import_program_data.py`
  - [ ] Similar structure to person data
  - [ ] Program-specific validation

### Validators
- [ ] Create `src/core/ports/validator.py` (expanded)
  - [ ] `IStructuralValidator` (CSV parsing)
  - [ ] `ISemanticValidator` (business rules)
- [ ] Create `src/infrastructure/validators/csv_validator.py`
  - [ ] Validate column presence
  - [ ] Type coercion errors
  - [ ] NULL handling
- [ ] Create `src/infrastructure/validators/lookup_validator.py`
  - [ ] Required fields
  - [ ] Code uniqueness per code set
- [ ] Create `src/infrastructure/validators/person_validator.py`
  - [ ] Birth date logic (not future)
  - [ ] Required demographics
  - [ ] Data quality flag interpretation

### Data Quality Reporting
- [ ] Create `src/application/data_quality_report.py`
  - [ ] Count records by quality level
  - [ ] Flag suspicious data patterns
  - [ ] Export report as JSON/CSV

### Testing
- [ ] Create `tests/unit/test_lookup_sorter.py`
  - [ ] Test dependency ordering
- [ ] Create `tests/unit/test_validators.py`
  - [ ] Test each validator class
- [ ] Create `tests/integration/test_csv_parsing.py`
  - [ ] Test reading actual CSV files
  - [ ] Test type coercion
  - [ ] Test error handling
- [ ] Create `tests/integration/test_import_workflow.py`
  - [ ] Test loading reference data
  - [ ] Test loading person data
  - [ ] Verify database state
  - [ ] Test error recovery

### Documentation
- [ ] Update `docs/CSV_MAPPING.md` (comprehensive column mapping)
- [ ] Create `docs/LOOKUP_DEPENDENCIES.md` (dependency graph)
- [ ] Update `docs/SETUP.md` with migration instructions
- [ ] Create `docs/DATA_QUALITY.md` (quality flag interpretation)

### Performance Testing
- [ ] Benchmark loading 1000 reference records
- [ ] Benchmark loading 1000 person records
- [ ] Measure memory usage
- [ ] Measure time per phase

**Completion Sign-off:**
- [ ] All checklist items complete
- [ ] Code review passed
- [ ] Integration tests passing (70%+ coverage)
- [ ] Performance benchmarks acceptable

---

## Phase 3: Relationships & Validation (Weeks 5-6)

**Objective:** Load enrollment, cohort, and validate referential integrity

### Database Schema
- [ ] Create migration: `005_create_enrollment_tables.py`
  - [ ] Enrollment, CourseTermAssociation, Cohort, CohortMembership, PersonProgram
  - [ ] FK constraints
  - [ ] Test migration

### Entity Models
- [ ] Create `src/core/entities/enrollment.py`
  - [ ] Enrollment, CourseTermAssociation
- [ ] Create `src/core/entities/cohort.py`
  - [ ] Cohort, CohortMembership
- [ ] Create `src/core/entities/person_program.py`
  - [ ] PersonProgram, PersonAcademicPeriod

### Repository Implementations
- [ ] Create repositories for each entity type
  - [ ] EnrollmentRepository
  - [ ] CohortRepository
  - [ ] PersonProgramRepository
  - [ ] All with FK validation

### Use Cases
- [ ] Create `src/core/use_cases/import_enrollment_data.py`
- [ ] Create `src/core/use_cases/import_cohort_data.py`
- [ ] Create `src/core/use_cases/import_person_program_data.py`
- [ ] All with `ImportResult` return type

### Referential Integrity Validation
- [ ] Create `src/core/use_cases/validate_referential_integrity.py`
  - [ ] Check all FKs exist
  - [ ] Identify orphaned records
  - [ ] Generate comprehensive report
- [ ] Create `src/application/orphan_detector.py`
  - [ ] Query for orphaned records by entity type
  - [ ] Export list with resolution suggestions

### Error Recovery
- [ ] Implement retry logic using `tenacity` library
  - [ ] Exponential backoff (1s, 2s, 4s)
  - [ ] Max 3 retries
  - [ ] Retry on OperationalError, DatabaseError
- [ ] Create `src/application/error_recovery.py`
  - [ ] Rollback on fatal errors
  - [ ] Log detailed error context
  - [ ] Suggest fixes for common issues

### Testing
- [ ] Create `tests/integration/test_referential_integrity.py`
  - [ ] Test FK validation
  - [ ] Test orphaned record detection
  - [ ] Test with intentional orphan records
- [ ] Create `tests/integration/test_error_recovery.py`
  - [ ] Test retry logic
  - [ ] Test rollback
  - [ ] Test graceful failure

### Documentation
- [ ] Update `docs/CSV_MAPPING.md` with all entity mappings
- [ ] Create `docs/REFERENTIAL_INTEGRITY.md` (FK rules, orphan handling)
- [ ] Create `docs/ERROR_HANDLING.md` (recovery strategies)
- [ ] Update `TROUBLESHOOTING.md` with Phase 3 issues

**Completion Sign-off:**
- [ ] All checklist items complete
- [ ] 70%+ test coverage
- [ ] Referential integrity tests passing
- [ ] Error recovery tested

---

## Phase 4: Advisor-Specific Data (Weeks 7-8)

**Objective:** Load degree planning, support, and prediction data

### Database Schema
- [ ] Create migration: `006_create_advisor_tables.py`
  - [ ] LearnerDegreePlan, LearnerDegreePlanItem, LearnerDegreePlanPreferences
  - [ ] PersonSupportAssignment, PersonSupportReferral
  - [ ] LearnerEarlyAlert, LearnerEarlyAlertActivity
  - [ ] LearnerSuccessPrediction, SuccessPredictionModel
  - [ ] FK constraints
  - [ ] Test migration

### Entity Models
- [ ] Create `src/core/entities/degree_plan.py`
  - [ ] LearnerDegreePlan, LearnerDegreePlanItem, LearnerDegreePlanPreferences
  - [ ] Revision tracking
  - [ ] Effective dating
- [ ] Create `src/core/entities/support.py`
  - [ ] PersonSupportAssignment, PersonSupportReferral
  - [ ] Primary within context flag
  - [ ] Effective dates
- [ ] Create `src/core/entities/early_alert.py`
  - [ ] LearnerEarlyAlert, LearnerEarlyAlertActivity
  - [ ] Alert triggers
  - [ ] Follow-up tracking
- [ ] Create `src/core/entities/prediction.py`
  - [ ] LearnerSuccessPrediction, SuccessPredictionModel
  - [ ] Score semantics
  - [ ] Probability tracking

### Repository Implementations
- [ ] Create `src/infrastructure/repositories/degree_plan_repository.py`
- [ ] Create `src/infrastructure/repositories/support_repository.py`
- [ ] Create `src/infrastructure/repositories/alert_repository.py`
- [ ] Create `src/infrastructure/repositories/prediction_repository.py`

### Use Cases
- [ ] Create `src/core/use_cases/import_degree_plan_data.py`
  - [ ] Validate plan consistency
  - [ ] Check item references
- [ ] Create `src/core/use_cases/import_support_data.py`
  - [ ] Validate assignment dates
  - [ ] Check role codes
- [ ] Create `src/core/use_cases/import_alert_data.py`
  - [ ] Validate alert triggers
  - [ ] Check activity linkage
- [ ] Create `src/core/use_cases/import_prediction_data.py`
  - [ ] Validate model versions
  - [ ] Score range checks

### Advisor-Specific Validators
- [ ] Create `src/infrastructure/validators/degree_plan_validator.py`
  - [ ] Item dates within term
  - [ ] Requirement references valid
  - [ ] Prerequisites satisfied
- [ ] Create `src/infrastructure/validators/support_validator.py`
  - [ ] Assignment dates valid (end > start)
  - [ ] Primary flag validation
  - [ ] Role codes exist
- [ ] Create `src/infrastructure/validators/alert_validator.py`
  - [ ] Trigger codes valid
  - [ ] Activity linked to alert

### Testing
- [ ] Create `tests/integration/test_degree_plan_import.py`
  - [ ] Test plan loading
  - [ ] Test consistency validation
  - [ ] Test advisor queries work
- [ ] Create `tests/integration/test_support_import.py`
  - [ ] Test assignment loading
  - [ ] Test referral loading
- [ ] Create `tests/integration/test_advisor_queries.py`
  - [ ] Query student degree plan
  - [ ] Query student support team
  - [ ] Query early alerts
  - [ ] Query success predictions

### Documentation
- [ ] Create `docs/ADVISOR_WORKFLOWS.md` (use cases, queries)
- [ ] Update `docs/CSV_MAPPING.md` with advisor entities
- [ ] Create `docs/ADVISOR_DATA_QUALITY.md`
- [ ] Update `TROUBLESHOOTING.md`

**Completion Sign-off:**
- [ ] All checklist items complete
- [ ] 75%+ test coverage
- [ ] Advisor queries tested and documented
- [ ] Data quality acceptable

---

## Phase 5: CLI & Documentation (Week 9)

**Objective:** Build CLI, finalize documentation, end-to-end testing

### CLI Implementation
- [ ] Create `src/cli/main.py` (Click-based)
  - [ ] `--csv-dir` option (required)
  - [ ] `--database-url` option (required)
  - [ ] `--tenant-id` option (required)
  - [ ] `--dry-run` flag (validation only)
  - [ ] `--skip-validation` flag (risky, not recommended)
  - [ ] `--verbose` flag (detailed logging)
- [ ] Add command documentation
  - [ ] Help text for each option
  - [ ] Usage examples
  - [ ] Error messages

### CLI Output & Reporting
- [ ] Create `src/cli/output_formatter.py`
  - [ ] Progress bar (using `tqdm`)
  - [ ] Phase start/end messages
  - [ ] Record count summaries
  - [ ] Error summaries
  - [ ] Color-coded warnings/errors
  - [ ] Audit trail ID output
- [ ] Implement JSON output mode (for scripting)
  - [ ] Structured results
  - [ ] Machine-readable error codes

### Audit Trail & Logging
- [ ] Create migration: `007_create_audit_tables.py`
  - [ ] import_audit_trail table (schema defined in techSpec1.md)
- [ ] Create `src/application/audit_logger.py`
  - [ ] Log import start/end
  - [ ] Log phase transitions
  - [ ] Log error details
  - [ ] Create audit trail record in database
- [ ] Configure structured JSON logging
  - [ ] Log level: INFO (normal), DEBUG (verbose), WARNING, ERROR
  - [ ] JSON format for all logs
  - [ ] Timestamp, level, message, context
  - [ ] Mask PII in logs

### Complete Import Service
- [ ] Update `src/application/import_service.py`
  - [ ] Integrate all 5 phases
  - [ ] Coordinate validators
  - [ ] Error handling and recovery
  - [ ] Progress reporting
  - [ ] Audit trail
- [ ] Add transaction management
  - [ ] Begin transaction at phase start
  - [ ] Commit on phase success
  - [ ] Rollback on phase failure
  - [ ] No partial updates

### End-to-End Testing
- [ ] Create `tests/integration/test_end_to_end.py`
  - [ ] Full import with sample data
  - [ ] Verify all tables populated
  - [ ] Check data counts
  - [ ] Verify advisor queries work
  - [ ] Check audit trail created
- [ ] Load and validate against GUIDE schema
  - [ ] Verify schema compliance
  - [ ] No extra tables/columns
  - [ ] All constraints applied
- [ ] Test error scenarios
  - [ ] Missing CSV files
  - [ ] Database connection failure
  - [ ] Duplicate records (recovery)
  - [ ] Missing FK references (warning)

### Performance Testing
- [ ] Benchmark full import (all 116 CSV files)
  - [ ] Measure total elapsed time
  - [ ] Time per phase
  - [ ] Records per minute
  - [ ] Peak memory usage
  - [ ] Goal: < 10 minutes total
- [ ] Optimize if needed
  - [ ] Batch size tuning
  - [ ] Index timing
  - [ ] Connection pooling
  - [ ] Query optimization

### Comprehensive Documentation
- [ ] Create `docs/SETUP.md` (environment setup)
- [ ] Create `docs/GETTING_STARTED.md` (first import)
- [ ] Create `docs/OPERATOR_GUIDE.md`
  - [ ] Step-by-step import instructions
  - [ ] Interpreting results
  - [ ] Checking audit trail
  - [ ] Common issues and fixes
- [ ] Create `docs/CSV_MAPPING.md` (complete)
  - [ ] All 116 files
  - [ ] Column mappings
  - [ ] Data types
  - [ ] NULL handling
- [ ] Create `docs/TROUBLESHOOTING.md` (comprehensive)
  - [ ] Common errors and solutions
  - [ ] Debug log interpretation
  - [ ] Recovery procedures
  - [ ] Support contacts
- [ ] Create `docs/GUIDE_SCHEMA_NOTES.md`
  - [ ] Entity relationships
  - [ ] Cardinality (1:1, 1:N, M:N)
  - [ ] FK constraints
  - [ ] Temporal rules
  - [ ] Audit metadata
- [ ] Create `docs/ADVISOR_WORKFLOWS.md`
  - [ ] Query examples
  - [ ] Workflow descriptions
  - [ ] Data quality caveats
- [ ] Update README.md
  - [ ] Project overview
  - [ ] Quick start
  - [ ] Documentation index
  - [ ] Contributing guidelines

### Configuration & Secrets Management
- [ ] Finalize `.env.example`
  - [ ] All required variables
  - [ ] Documentation for each
  - [ ] Default values where applicable
- [ ] Document `.env` setup
  - [ ] How to create `.env` from example
  - [ ] Required vs. optional variables
  - [ ] Where to get values (DB connection, etc.)

### Code Quality & Release
- [ ] Run full test suite: `pytest tests/`
  - [ ] 80%+ coverage target
  - [ ] All tests passing
- [ ] Run linter: `flake8 src/`
  - [ ] Fix all violations
- [ ] Run type checker: `mypy src/`
  - [ ] Fix all type errors
- [ ] Code formatting: `black src/`
  - [ ] Consistent style
- [ ] Security scan (if available)
  - [ ] Check for known vulnerabilities
  - [ ] No hardcoded secrets
- [ ] Create CHANGELOG.md
  - [ ] Version 1.0 features
  - [ ] Known limitations
  - [ ] Future roadmap

### Deployment Readiness
- [ ] Docker build (if needed)
  - [ ] Dockerfile
  - [ ] Docker Compose for local dev
  - [ ] Production image ready
- [ ] CI/CD verification
  - [ ] GitHub Actions running tests
  - [ ] Automated linting
  - [ ] Automated type checking
- [ ] Deployment documentation
  - [ ] How to deploy to production
  - [ ] Database backup/recovery
  - [ ] Rollback procedures

### Knowledge Transfer
- [ ] Create video walkthrough (optional)
  - [ ] Running first import
  - [ ] Interpreting results
  - [ ] Troubleshooting
- [ ] Create runbook
  - [ ] Day-1 import steps
  - [ ] Regular maintenance
  - [ ] Monitoring and alerts
- [ ] Schedule training session (optional)
  - [ ] Operators/DBAs
  - [ ] Advisors (query examples)

### Final Validation
- [ ] Test import with full dataset
  - [ ] All 116 CSV files
  - [ ] Run end-to-end
  - [ ] Verify data integrity
  - [ ] Check advisor queries
- [ ] Compare with GUIDE schema
  - [ ] All tables present
  - [ ] All columns present
  - [ ] All constraints enforced
- [ ] Manual data spot-checks
  - [ ] Random record sampling
  - [ ] Verify data accuracy
  - [ ] Check audit trail
- [ ] Get sign-off from stakeholders

**Completion Sign-off:**
- [ ] All checklist items complete
- [ ] 80%+ test coverage achieved
- [ ] CLI working as designed
- [ ] Documentation complete and reviewed
- [ ] Performance meets < 10 minute SLA
- [ ] End-to-end test passing
- [ ] Stakeholder sign-off
- [ ] Ready for production deployment

---

## Post-Implementation (Ongoing)

### Monitoring & Maintenance
- [ ] Set up monitoring for imports
  - [ ] Success/failure rates
  - [ ] Duration trends
  - [ ] Data quality over time
- [ ] Regular testing
  - [ ] Monthly test import
  - [ ] Sample data validation
  - [ ] Query verification
- [ ] Documentation updates
  - [ ] Add new CSV files as they appear
  - [ ] Update troubleshooting guide
  - [ ] Document any customizations

### Future Enhancements (Phase 6+)
- [ ] Incremental update support
  - [ ] Detect changes since last import
  - [ ] Upsert instead of full refresh
- [ ] Real-time integration
  - [ ] Event streaming (Kafka)
  - [ ] Change data capture
- [ ] Data quality dashboard
  - [ ] Real-time monitoring
  - [ ] Quality metrics
  - [ ] Issue alerts
- [ ] Advisor API
  - [ ] GraphQL or REST API
  - [ ] Direct database access
  - [ ] Integrated dashboard

---

## Notes

- **Mark items as complete** by checking the box `[x]`
- **Track blockers** - if something is blocked, note the reason and dependency
- **Ask for help** - reach out to team members if you get stuck
- **Update dates** - adjust timelines if needed, but try to stay close to plan
- **Celebrate progress** - each phase is a significant milestone!

---

**Checklist Version:** 1.0  
**Last Updated:** 2026-11-08  
**Owner:** [To be assigned]  
