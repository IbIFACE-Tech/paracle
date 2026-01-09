# Migration Script Template
# Copy and modify this template for your migration

"""Migration from v[OLD] to v[NEW]

Revision ID: [UNIQUE_ID]
Revises: [PREVIOUS_REVISION]
Create Date: [DATE]

Description:
- [Change 1]
- [Change 2]
"""

import sqlalchemy as sa
from alembic import op

# Revision identifiers
revision = "[UNIQUE_ID]"
down_revision = "[PREVIOUS_REVISION]"
branch_labels = None
depends_on = None


def upgrade():
    """Upgrade to v[NEW]."""

    # Example: Add new table
    op.create_table(
        "new_table",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # Example: Add column to existing table
    op.add_column("existing_table", sa.Column("new_column", sa.String(), nullable=True))

    # Example: Create index
    op.create_index("ix_new_table_name", "new_table", ["name"])

    # Example: Data migration
    connection = op.get_bind()
    connection.execute(
        sa.text(
            "UPDATE existing_table SET new_column = 'default' WHERE new_column IS NULL"
        )
    )

    # Example: Make column non-nullable after data migration
    op.alter_column("existing_table", "new_column", nullable=False)


def downgrade():
    """Downgrade to v[OLD]."""

    # Reverse all changes in opposite order
    op.alter_column("existing_table", "new_column", nullable=True)
    op.drop_index("ix_new_table_name", "new_table")
    op.drop_column("existing_table", "new_column")
    op.drop_table("new_table")
