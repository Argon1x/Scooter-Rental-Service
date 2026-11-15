from alembic import op
import sqlalchemy as sa

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("user_type", sa.String(), nullable=False),
    )
    op.create_table(
        "scooters",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("model", sa.String(), nullable=False),
        sa.Column("charge_level", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("status", sa.String(), nullable=False, server_default="available"),
        sa.Column("current_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("scooters")
    op.drop_table("users")
