from alembic import op
import sqlalchemy as sa

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "rentals",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("scooter_id", sa.Integer(), sa.ForeignKey("scooters.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("battery_used", sa.Integer(), nullable=True, server_default="0"),
    )

    connection = op.get_bind()
    scooters_table = sa.table(
        "scooters",
        sa.column("id", sa.Integer),
        sa.column("current_user_id", sa.Integer),
        sa.column("status", sa.String),
    )
    rentals_table = sa.table(
        "rentals",
        sa.column("user_id", sa.Integer),
        sa.column("scooter_id", sa.Integer),
        sa.column("status", sa.String),
        sa.column("battery_used", sa.Integer),
    )

    active_scooters = connection.execute(
        sa.select(scooters_table.c.id, scooters_table.c.current_user_id).where(
            scooters_table.c.status == "rented",
            scooters_table.c.current_user_id.isnot(None),
        )
    ).fetchall()

    for row in active_scooters:
        connection.execute(
            rentals_table.insert().values(
                user_id=row.current_user_id,
                scooter_id=row.id,
                status="active",
                battery_used=0,
            )
        )


def downgrade() -> None:
    op.drop_table("rentals")
