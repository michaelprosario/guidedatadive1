"""Add indexes for common tenant-scoped advisor joins."""

from alembic import op

revision = "002_advisor_indexes"
down_revision = "001_initial"
branch_labels = None
depends_on = None

INDEXES = (
    ("ix_enrollment_person", "Enrollment", ["TenantIdentifier", "PersonIdentifier"]),
    ("ix_person_program_person", "PersonProgram", ["TenantIdentifier", "PersonIdentifier"]),
    ("ix_degree_plan_person", "LearnerDegreePlan", ["TenantIdentifier", "PersonIdentifier"]),
    ("ix_support_assignment_person", "PersonSupportAssignment", ["TenantIdentifier", "PersonIdentifier"]),
    ("ix_early_alert_person", "LearnerEarlyAlert", ["TenantIdentifier", "PersonIdentifier"]),
    ("ix_prediction_person", "LearnerSuccessPrediction", ["TenantIdentifier", "PersonIdentifier"]),
)


def upgrade():
    for name, table, columns in INDEXES:
        op.create_index(name, table, columns, schema="guide_public")


def downgrade():
    for name, table, _ in reversed(INDEXES):
        op.drop_index(name, table_name=table, schema="guide_public")
