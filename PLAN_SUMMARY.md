# GUIDE Data Import Program - Plan Summary

**Status:** ✅ Technical Planning Complete  
**Date:** 2026-11-08  
**Prepared for:** 2026-11 DevFest Florida  

---

## Overview

A comprehensive technical approach has been developed for importing **116 CSV files** containing GUIDE v1.0.0 data model into PostgreSQL using Python, organized with clean architecture principles.

**Key Deliverables:**
1. ✅ [techSpec1.md](/workspaces/guidedatadive1/techSpec1.md) - Complete technical specification (628 lines)
2. ✅ [IMPLEMENTATION_GUIDE.md](/workspaces/guidedatadive1/IMPLEMENTATION_GUIDE.md) - Step-by-step implementation guide
3. ✅ [ARCHITECTURE_DIAGRAM.md](/workspaces/guidedatadive1/ARCHITECTURE_DIAGRAM.md) - Visual architecture and data flow diagrams

---

## Core Approach

### Clean Architecture (4 Layers)

```
┌─────────────────────────────────────────┐
│  CLI Layer (Click-based commands)       │ ◄── User interaction
├─────────────────────────────────────────┤
│  Application Layer (Orchestration)      │ ◄── Workflow coordination
├─────────────────────────────────────────┤
│  Core Layer (Business Logic)            │ ◄── Domain entities & use cases
│  [Zero framework dependencies]          │    (testable, maintainable)
├─────────────────────────────────────────┤
│  Infrastructure Layer (Technical)       │ ◄── Database, CSV parsing
└─────────────────────────────────────────┘
```

### Key Design Principles

| Principle | Benefit |
|-----------|---------|
| **Dependency Inversion** | Core layer is framework-independent; easy to test |
| **CQRS Pattern** | All use cases accept Command/Query objects for clarity |
| **Result Objects** | Standardized error handling and response format |
| **Multi-Level Validation** | Structural → Semantic → Referential → Data Quality |
| **Phased Loading** | Risk-managed rollout; dependencies respected |
| **Audit Trails** | Every import tracked; traceability for compliance |

---

## Data Characteristics (from Research)

### What We're Importing

| Category | Count | Purpose |
|----------|-------|---------|
| Reference/Lookup Tables | 27 | Codes, statuses, types (e.g., RoleL, CourseStatusLookup) |
| Person Data | 11 | Demographics, contact, employment, housing |
| Academic Data | 23 | Catalog, requirements, curriculum, assessment |
| Enrollment Data | 15 | Enrollments, attendance, credits, outcomes |
| Advisor Support | 12 | Assignments, referrals, alerts, predictions |
| Career & Transfer | 7 | Pathways, job mappings, transfer evaluations |
| Administrative | 11 | Tenants, organizations, sites, terms, roles |

### Critical Observations

1. **Multi-Tenant:** Every record has `TenantIdentifier`
2. **Audit Metadata:** Created/Updated/Deleted dates and user tracking
3. **Source Lineage:** `SourceSystemIdentifier` and `SourceSystemKeyValue` preserved
4. **Data Quality:** Quality flags on sensitive fields (e.g., `BirthDateQuality`)
5. **Temporal Relationships:** Many entities use `RecordStartDate` / `RecordEndDate`
6. **Rich Relationships:** Complex FK patterns (29 lookup dependencies)

---

## Import Workflow (8 Phases)

```
1. Bootstrap & Configuration
   └─► Load config, verify connectivity, initialize migrations

2. Schema Initialization
   └─► Apply Alembic migrations, create tables and indexes

3. Load Reference Data (Priority 1)
   └─► ReferenceCodeSet, ReferenceCodeValue, all 27 lookups
       (sorted by dependency)

4. Load Core Entities (Priority 2)
   └─► PersonLookup, Organization, Program, AcademicCatalog
       (validate PK uniqueness, data quality)

5. Load Relationships (Priority 3)
   └─► Enrollment, PersonProgram, Cohort, CourseTermAssoc
       (validate FK constraints, cardinality)

6. Load Advisor-Specific Data (Priority 4)
   └─► LearnerDegreePlan, PersonSupportAssignment, LearnerEarlyAlert
       (validate consistency, completeness)

7. Post-Load Validation
   └─► Check referential integrity, identify orphaned records
       (generate data quality report)

8. Finalization
   └─► Create audit trail, log statistics, return status
```

---

## Technology Stack

```
Python 3.11+              Core language
PostgreSQL 15+            Relational database
SQLAlchemy 2.0+           ORM
Alembic 1.13+             Schema migrations
Pandas 2.1+               CSV parsing (efficient bulk ops)
Pydantic 2.0+             Data validation
Click 8.1+                CLI framework
Tenacity 8.2+             Retry logic

Testing:
  pytest 7.4+             Test framework
  pytest-cov 4.1+         Coverage reporting
  pytest-mock 3.12+       Mocking utilities
```

---

## Project Structure

```
src/
├── core/                    ◄── Business logic (framework-independent)
│   ├── entities/            (Domain models: Person, Program, etc.)
│   ├── use_cases/           (Import operations: CQRS pattern)
│   └── ports/               (Interfaces: IRepository, IValidator)
│
├── infrastructure/          ◄── Technical implementation
│   ├── adapters/            (CSV reader, Database connector)
│   ├── repositories/        (SQLAlchemy implementations)
│   ├── config/              (Database configuration)
│   └── migrations/          (Alembic schema versions)
│
├── application/             ◄── Orchestration layer
│   ├── import_service.py    (Main workflow coordinator)
│   ├── error_handler.py     (Error handling & recovery)
│   └── progress_tracker.py  (Audit trail & metrics)
│
└── cli/                     ◄── User interface
    ├── main.py              (Click entry point)
    └── output_formatter.py  (Console output & reporting)

tests/
├── unit/                    (Business logic tests)
├── integration/             (End-to-end workflows)
└── fixtures/                (Sample data, CSV files)

config/
├── database.ini             (DB connection settings)
├── alembic.ini              (Migration config)
└── logging.yaml             (Logging configuration)

docs/
├── CSV_MAPPING.md           (Column-by-column mapping)
├── GUIDE_SCHEMA_NOTES.md    (Entity relationships)
└── TROUBLESHOOTING.md       (Common issues & solutions)
```

---

## Implementation Timeline

| Phase | Weeks | Deliverables | Status |
|-------|-------|--------------|--------|
| 1. Foundation | 1-2 | Repository structure, base classes, CSV adapter, unit tests | Planning |
| 2. Reference Data | 3-4 | Lookup table imports, dependency ordering, integration tests | Planning |
| 3. Relationships | 5-6 | Enrollment/cohort loading, referential validation, error recovery | Planning |
| 4. Advisor Data | 7-8 | Degree plans, support assignments, early alerts, predictions | Planning |
| 5. CLI & Docs | 9 | Command-line interface, operator guide, end-to-end testing | Planning |

---

## Success Criteria

✅ All 116 CSV files successfully loaded  
✅ Referential integrity maintained (0 orphaned records)  
✅ Data quality report generated and reviewed  
✅ Advisor queries return correct results  
✅ Import completes in < 10 minutes  
✅ 80%+ test coverage  
✅ No PII exposed in logs  
✅ Complete operator documentation  

---

## Key Advantages of This Approach

### 1. **Maintainability**
- Clear separation of concerns (4 layers)
- Business logic isolated from frameworks
- Easy to understand and modify

### 2. **Testability**
- Core layer testable without database
- Mock implementations for dependencies
- 80%+ coverage target achievable
- Integration tests with fixtures

### 3. **Scalability**
- Phased loading respects dependencies
- Bulk operations for performance
- Index creation optimized
- Foundation for incremental updates

### 4. **Reliability**
- Multi-level validation (structural, semantic, referential, data quality)
- Error recovery with retry logic
- Audit trails for compliance
- Transaction rollback on failures

### 5. **Compliance**
- Tenant isolation enforced at data layer
- PII masking in logs
- Complete audit trail
- Source system lineage preserved

---

## Advisor Workflow Support

The import program specifically enables these advisor workflows:

| Workflow | Supported By |
|----------|--------------|
| **Requirement Progress** | PersonProgramProgressEvaluation, PersonProgramRequirementEvaluation |
| **Degree Planning** | LearnerDegreePlan, LearnerDegreePlanItem, LearnerDegreePlanPreferences |
| **Transfer Credit** | LearnerTransferCreditEvaluation, LearnerAcademicCreditTransferEvaluation |
| **Support Assignments** | PersonSupportAssignment, PersonSupportReferral |
| **Early Alerts** | LearnerEarlyAlert, LearnerEarlyAlertActivity |
| **Predictive Insights** | LearnerSuccessPrediction, SuccessPredictionModel |
| **Career Mapping** | CareerPathway, CareerPathwayComponent, CareerPathwayJob |

---

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| Large dataset (116 files) | Phased loading by priority; performance optimized |
| Complex dependencies | Topological ordering; dependency validator |
| Data quality issues | Multi-level validation; detailed error reporting |
| PII exposure | Masking in logs; audit trail tracking |
| Schema evolution | Alembic migrations; version control |
| Operator errors | CLI validation; dry-run mode; comprehensive docs |

---

## Next Steps

### Immediate (Week 1)
1. ✅ Review technical specification with stakeholders
2. ⏳ Approve architecture and design decisions
3. ⏳ Set up PostgreSQL development environment
4. ⏳ Create GitHub repository with branch protection

### Short-term (Weeks 2-3)
1. ⏳ Implement Phase 1 (Foundation)
2. ⏳ Set up CI/CD pipeline
3. ⏳ Create Alembic migrations
4. ⏳ Write unit tests for entities

### Medium-term (Weeks 4-6)
1. ⏳ Implement Phase 2 (Reference Data)
2. ⏳ Implement Phase 3 (Relationships)
3. ⏳ Integration testing
4. ⏳ Performance optimization

### Long-term (Weeks 7-9)
1. ⏳ Implement Phase 4 (Advisor Data)
2. ⏳ Implement Phase 5 (CLI & Docs)
3. ⏳ End-to-end testing
4. ⏳ Production readiness review

---

## Questions & Clarifications Needed

Before implementation, clarify:

1. **PostgreSQL Environment**
   - Development machine or managed RDS?
   - Connection pooling requirements?
   - Backup/recovery strategy?

2. **Data Validation**
   - Strictness level for data quality flags?
   - Tolerance for orphaned records?
   - How to handle duplicate keys?

3. **Incremental Updates**
   - Will the program be re-run with fresh exports?
   - Should it support incremental updates or full refreshes?
   - How to handle deleted records?

4. **Access & Security**
   - Who can trigger imports?
   - Audit trail retention policy?
   - Log retention (sensitive data)?

5. **Performance**
   - SLA for import completion?
   - Acceptable memory usage?
   - Real-time vs. batch constraints?

---

## Resources Required

### Personnel
- **Lead Engineer:** 1 FTE (architecture, Core layer implementation)
- **Backend Engineer:** 1 FTE (Infrastructure, testing)
- **Database Admin:** 0.5 FTE (schema review, optimization)

### Infrastructure
- Development PostgreSQL instance
- CI/CD pipeline (GitHub Actions or similar)
- Logging/monitoring (structured JSON logs)
- Python 3.11+ environment

### Time
- 9 weeks for full implementation
- 2-3 weeks for knowledge transfer
- Ongoing: monitoring, maintenance, documentation

---

## References

**From This Repository:**
- [research/dataModelReviewForAdvisor.md](/workspaces/guidedatadive1/research/dataModelReviewForAdvisor.md) - Data model analysis
- [specs/clean_architecture.md](/workspaces/guidedatadive1/specs/clean_architecture.md) - Architecture principles
- [promptLog.txt](/workspaces/guidedatadive1/promptLog.txt) - Original requirements

**External References:**
- [GUIDE v1.0.0 Schema](./2026-11\ DevFest\ Florida/GUIDE\ Materials/guide_data_model_schema_v1.0.0.json)
- [CSV Data Files](./2026-11\ DevFest\ Florida/GUIDE\ Materials/csv/) (116 files)

**Documentation Artifacts:**
- [techSpec1.md](/workspaces/guidedatadive1/techSpec1.md) - Complete technical specification
- [IMPLEMENTATION_GUIDE.md](/workspaces/guidedatadive1/IMPLEMENTATION_GUIDE.md) - Implementation checklist and patterns
- [ARCHITECTURE_DIAGRAM.md](/workspaces/guidedatadive1/ARCHITECTURE_DIAGRAM.md) - Visual diagrams

---

## Conclusion

This technical specification provides a **production-ready roadmap** for building a robust, maintainable GUIDE data import program. The clean architecture approach ensures:

- ✅ Core business logic is framework-independent and easily testable
- ✅ Clear separation of concerns across four layers
- ✅ Multi-level validation for data quality assurance
- ✅ Comprehensive audit trails for compliance
- ✅ Risk-managed phased implementation
- ✅ Strong foundation for future enhancements

The 9-week phased implementation plan provides a realistic timeline with clear milestones and deliverables. All necessary design patterns (CQRS, Result objects, Dependency Inversion) have been specified to enable a professional, enterprise-grade system.

**Ready to proceed to Phase 1: Foundation** 🚀

---

**Document Version:** 1.0  
**Last Updated:** 2026-11-08  
**Next Review:** After stakeholder approval  
