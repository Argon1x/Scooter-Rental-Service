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
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("scooter_id", sa.Integer(), sa.ForeignKey("scooters.id", ondelete="SET NULL"), nullable=True),
        sa.Column("user_name", sa.String(), nullable=True),
        sa.Column("scooter_model", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("battery_used", sa.Integer(), nullable=True, server_default="0"),
    )

    connection = op.get_bind()
    scooters_table = sa.table(
        "scooters",
        sa.column("id", sa.Integer),
        sa.column("model", sa.String),
        sa.column("current_user_id", sa.Integer),
        sa.column("status", sa.String),
    )
    users_table = sa.table(
        "users",
        sa.column("id", sa.Integer),
        sa.column("name", sa.String),
    )
    rentals_table = sa.table(
        "rentals",
        sa.column("user_id", sa.Integer),
        sa.column("scooter_id", sa.Integer),
        sa.column("user_name", sa.String),
        sa.column("scooter_model", sa.String),
        sa.column("status", sa.String),
        sa.column("battery_used", sa.Integer),
    )

    active_scooters = connection.execute(
        sa.select(scooters_table.c.id, scooters_table.c.model, scooters_table.c.current_user_id).where(
            scooters_table.c.status == "rented",
            scooters_table.c.current_user_id.isnot(None),
        )
    ).fetchall()

    for row in active_scooters:
        user_row = connection.execute(
            sa.select(users_table.c.name).where(users_table.c.id == row.current_user_id)
        ).fetchone()
        u_name = user_row[0] if user_row else None
        connection.execute(
            rentals_table.insert().values(
                user_id=row.current_user_id,
                scooter_id=row.id,
                user_name=u_name,
                scooter_model=row.model,
                status="active",
                battery_used=0,
            )
        )


def downgrade() -> None:
    op.drop_table("rentals")
