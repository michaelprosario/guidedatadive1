# Implementation Guide: GUIDE Data Import Program

Quick reference for building the import program outlined in [techSpec1.md](/workspaces/guidedatadive1/techSpec1.md).

---

## Quick Start

### 1. Project Setup

```bash
# Create project structure
mkdir -p src/{core,infrastructure,application,cli}/{entities,use_cases,repositories,adapters,ports,config,migrations}
mkdir -p tests/{unit,integration,fixtures}
mkdir -p config docs

# Create Python files
touch src/__init__.py
touch src/core/__init__.py
touch src/core/entities/__init__.py
touch src/core/use_cases/__init__.py
touch src/core/ports/__init__.py
# ... repeat for other directories
```

### 2. Dependencies (requirements.txt)

```txt
# Core
Python==3.11+

# Database
sqlalchemy==2.0.23
alembic==1.13.1
psycopg2-binary==2.9.9

# Data Processing
pandas==2.1.3
pydantic==2.5.0

# CLI & Utilities
click==8.1.7
python-dotenv==1.0.0
tenacity==8.2.3

# Development & Testing
pytest==7.4.3
pytest-cov==4.1.0
pytest-mock==3.12.0
black==23.11.0
flake8==6.1.0
mypy==1.7.1
```

---

## Architecture Layers

### Layer 1: Core (src/core/)

**Responsibility:** Pure business logic, zero framework dependencies

#### Entities

```python
# src/core/entities/person.py
from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional

@dataclass
class Person:
    """Domain entity for GUIDE Person"""
    tenant_id: str
    person_id: str
    first_name: str
    last_name: str
    birth_date: Optional[date]
    source_system_id: str
    source_system_key_value: str
    status: str
    created_by: str
    created_date: datetime
    
    def is_active(self) -> bool:
        return self.status == "Active"
```

#### Ports (Interfaces)

```python
# src/core/ports/repository.py
from abc import ABC, abstractmethod
from typing import List, Optional, Generic, TypeVar

T = TypeVar('T')

class IRepository(ABC, Generic[T]):
    @abstractmethod
    async def add(self, entity: T) -> None:
        pass
    
    @abstractmethod
    async def get_by_id(self, id: str) -> Optional[T]:
        pass
    
    @abstractmethod
    async def get_all(self) -> List[T]:
        pass
```

#### Use Cases

```python
# src/core/use_cases/import_reference_data.py
from dataclasses import dataclass
from typing import List

@dataclass
class ImportReferenceDataCommand:
    csv_directory: str
    reference_tables: List[str]
    skip_if_exists: bool = False

@dataclass
class ImportResult:
    success: bool
    records_processed: int
    records_failed: int
    warnings: List[str]
    errors: List[str]

class ImportReferenceDataUseCase:
    def __init__(self, repository):
        self.repository = repository
    
    async def execute(self, command: ImportReferenceDataCommand) -> ImportResult:
        # Business logic here
        pass
```

### Layer 2: Infrastructure (src/infrastructure/)

**Responsibility:** Database access, CSV parsing, external concerns

#### CSV Reader Adapter

```python
# src/infrastructure/adapters/csv_reader.py
import pandas as pd
from pathlib import Path
from typing import Iterator, Dict, Any

class CSVReader:
    def read_file(self, file_path: str) -> pd.DataFrame:
        """Read CSV file with GUIDE data"""
        df = pd.read_csv(file_path, dtype=str)
        return df
    
    def read_directory(self, dir_path: str, pattern: str = "*.csv") -> Iterator[tuple[str, pd.DataFrame]]:
        """Iterate through CSV files in directory"""
        path = Path(dir_path)
        for csv_file in path.glob(pattern):
            yield csv_file.stem, self.read_file(str(csv_file))
```

#### Database Repository Implementation

```python
# src/infrastructure/repositories/person_repository.py
from sqlalchemy import create_engine, Column, String, Date, DateTime, select
from sqlalchemy.orm import sessionmaker, declarative_base
from typing import Optional, List
from core.entities.person import Person
from core.ports.repository import IRepository

Base = declarative_base()

class PersonORM(Base):
    """SQLAlchemy ORM model for Person"""
    __tablename__ = "person_lookup"
    
    tenant_id = Column(String, primary_key=True)
    person_id = Column(String, primary_key=True)
    first_name = Column(String)
    last_name = Column(String)
    birth_date = Column(Date)
    source_system_id = Column(String)
    source_system_key_value = Column(String)
    status = Column(String)
    created_by = Column(String)
    created_date = Column(DateTime)

class PersonRepository(IRepository[Person]):
    def __init__(self, session):
        self.session = session
    
    async def add(self, entity: Person) -> None:
        orm_model = PersonORM(**entity.__dict__)
        self.session.add(orm_model)
        await self.session.commit()
    
    async def get_by_id(self, person_id: str) -> Optional[Person]:
        stmt = select(PersonORM).where(PersonORM.person_id == person_id)
        result = await self.session.execute(stmt)
        row = result.scalars().first()
        if row:
            return Person(**row.__dict__)
        return None
```

### Layer 3: Application (src/application/)

**Responsibility:** Workflow orchestration, error handling

```python
# src/application/import_service.py
from typing import List
from infrastructure.repositories.person_repository import PersonRepository
from core.use_cases.import_reference_data import ImportReferenceDataUseCase

class ImportService:
    def __init__(self, person_repo: PersonRepository):
        self.person_repo = person_repo
    
    async def run_import(self, csv_directory: str) -> dict:
        """Orchestrate the entire import workflow"""
        results = {
            "phase_1_reference_data": None,
            "phase_2_persons": None,
            "phase_3_relationships": None,
            "validation": None
        }
        
        # Phase 1: Reference data
        ref_use_case = ImportReferenceDataUseCase(self.person_repo)
        results["phase_1_reference_data"] = await ref_use_case.execute(...)
        
        # Phase 2: Person data
        # ... etc
        
        return results
```

### Layer 4: CLI (src/cli/)

**Responsibility:** User interface, argument parsing

```python
# src/cli/main.py
import click
from application.import_service import ImportService

@click.command()
@click.option('--csv-dir', required=True, help='Path to CSV directory')
@click.option('--database-url', required=True, help='PostgreSQL connection string')
@click.option('--dry-run', is_flag=True, help='Validate without loading')
def import_guide_data(csv_dir: str, database_url: str, dry_run: bool):
    """Import GUIDE data from CSV files into PostgreSQL"""
    service = ImportService(database_url)
    result = service.run_import(csv_dir, dry_run=dry_run)
    
    click.echo("Import completed!")
    click.echo(f"Records processed: {result['total_records']}")
    click.echo(f"Records failed: {result['records_failed']}")
    
    if result['warnings']:
        click.echo("\nWarnings:")
        for warning in result['warnings']:
            click.echo(f"  - {warning}")

if __name__ == '__main__':
    import_guide_data()
```

---

## Implementation Checklist

### Phase 1: Foundation (Weeks 1-2)

- [ ] Create project structure
- [ ] Set up Git repository and `.gitignore`
- [ ] Create `requirements.txt` and virtual environment
- [ ] Configure `.env` file for database connection
- [ ] Create Alembic migrations directory
- [ ] Implement base entity class
- [ ] Implement base repository interface
- [ ] Implement CSV reader adapter
- [ ] Write unit tests for entity creation
- [ ] Set up pytest and coverage reporting

**Key Files:**
- `src/core/entities/__init__.py` (base class)
- `src/core/ports/repository.py` (interface)
- `src/infrastructure/adapters/csv_reader.py`
- `tests/unit/test_entities.py`

### Phase 2: Reference Data & Core Entities (Weeks 3-4)

- [ ] Create all lookup entity models
- [ ] Implement reference data repository
- [ ] Create import use case for ReferenceCodeSet
- [ ] Create import use case for all lookup tables
- [ ] Implement dependency ordering logic
- [ ] Add validation for lookup data
- [ ] Create integration tests
- [ ] Document CSV mappings

**Key Files:**
- `src/core/entities/reference_data.py`
- `src/core/use_cases/import_lookup_tables.py`
- `src/infrastructure/repositories/reference_data_repository.py`
- `docs/CSV_MAPPING.md`

### Phase 3: Relationships & Validation (Weeks 5-6)

- [ ] Implement enrollment entity
- [ ] Implement relationship loading use cases
- [ ] Create referential integrity validator
- [ ] Implement orphaned record detector
- [ ] Add data quality reporting
- [ ] Create retry logic with tenacity
- [ ] Integration tests for relationships

### Phase 4: Advisor-Specific Data (Weeks 7-8)

- [ ] Implement degree plan entities
- [ ] Implement support assignment entities
- [ ] Create advisor-specific validators
- [ ] Add early alert and prediction loading
- [ ] Create advisor query performance tests

### Phase 5: CLI & Documentation (Week 9)

- [ ] Implement Click CLI with all options
- [ ] Add progress bar/reporting
- [ ] Create operator guide
- [ ] Create troubleshooting guide
- [ ] End-to-end test with full dataset
- [ ] Performance benchmark

---

## Common Patterns

### Error Handling Pattern

```python
# In use case
try:
    result = await self.repository.add(entity)
    return ImportResult(success=True, records_processed=1, ...)
except IntegrityError as e:
    logger.warning(f"Duplicate key: {e}")
    return ImportResult(success=False, warnings=[str(e)], ...)
except DatabaseError as e:
    logger.error(f"Database error: {e}")
    raise  # Fatal error
```

### Validation Pattern

```python
# In entity
class Person:
    def validate(self) -> List[str]:
        errors = []
        if not self.person_id:
            errors.append("person_id is required")
        if self.birth_date and self.birth_date > date.today():
            errors.append("birth_date cannot be in the future")
        return errors

# In use case
errors = person.validate()
if errors:
    return ImportResult(success=False, errors=errors)
```

### Bulk Load Pattern

```python
# In repository (for large datasets)
def bulk_insert(self, entities: List[T], batch_size: int = 1000):
    for i in range(0, len(entities), batch_size):
        batch = entities[i:i + batch_size]
        self.session.bulk_insert_mappings(self.orm_class, 
            [e.__dict__ for e in batch])
        self.session.commit()
```

---

## Testing Template

```python
# tests/unit/test_person_import.py
import pytest
from datetime import date
from core.entities.person import Person
from core.use_cases.import_reference_data import ImportReferenceDataCommand, ImportResult

@pytest.fixture
def sample_person():
    return Person(
        tenant_id="test-tenant",
        person_id="P001",
        first_name="John",
        last_name="Doe",
        birth_date=date(1990, 1, 1),
        source_system_id="SS-001",
        source_system_key_value="KEY001",
        status="Active",
        created_by="test",
        created_date=datetime.now()
    )

def test_person_is_active(sample_person):
    assert sample_person.is_active() == True

def test_person_validation(sample_person):
    errors = sample_person.validate()
    assert len(errors) == 0

# tests/integration/test_import_workflow.py
@pytest.mark.asyncio
async def test_import_reference_data(mock_repository):
    use_case = ImportReferenceDataUseCase(mock_repository)
    command = ImportReferenceDataCommand(
        csv_directory="tests/fixtures/csv",
        reference_tables=["ReferenceCodeSet"]
    )
    
    result = await use_case.execute(command)
    
    assert result.success == True
    assert result.records_processed > 0
```

---

## Environment Configuration

```bash
# .env file
DATABASE_URL=postgresql://user:password@localhost:5432/guide_db
GUIDE_CSV_PATH=./2026-11\ DevFest\ Florida/GUIDE\ Materials/csv
LOG_LEVEL=INFO
ENVIRONMENT=development
```

---

## Running the Import

```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Dry run (validation only)
python src/cli/main.py --csv-dir "$GUIDE_CSV_PATH" --database-url "$DATABASE_URL" --dry-run

# Full import
python src/cli/main.py --csv-dir "$GUIDE_CSV_PATH" --database-url "$DATABASE_URL"

# Run tests
pytest tests/ --cov=src --cov-report=html
```

---

## Performance Tips

1. **Index after bulk load** (not before)
2. **Use COPY for tables > 10K rows**
3. **Batch in transactions of 1000-5000 rows**
4. **Parallelize independent entity types**
5. **Monitor memory usage** (important with pandas)
6. **Vacuum PostgreSQL after large import**

---

## Troubleshooting

See [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) for common issues and solutions.

---

**For detailed architecture and design decisions, see [techSpec1.md](/workspaces/guidedatadive1/techSpec1.md)**
