"""Create traffic_observations table for TomTom collector.

Revision ID: 0002_create_traffic_observations
Revises: 0001_create_stations_and_aqi_observations
Create Date: 2026-10-21 22:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0002_create_traffic_observations"
down_revision: Union[str, None] = "0001_create_stations_and_aqi_observations"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "traffic_observations",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True, nullable=False),
        sa.Column("point_id", sa.String(length=64), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("current_speed", sa.Float(), nullable=True),
        sa.Column("free_flow_speed", sa.Float(), nullable=True),
        sa.Column("current_travel_time", sa.Float(), nullable=True),
        sa.Column("free_flow_travel_time", sa.Float(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("road_closure", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("frc", sa.String(length=32), nullable=True),
        sa.Column("source", sa.String(length=32), server_default="tomtom", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("point_id", "timestamp", name="uq_traffic_point_timestamp"),
    )
    op.create_index("ix_traffic_observations_point_id", "traffic_observations", ["point_id"], unique=False)
    op.create_index("ix_traffic_observations_timestamp", "traffic_observations", ["timestamp"], unique=False)
    op.create_index("ix_traffic_point_time", "traffic_observations", ["point_id", "timestamp"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_traffic_point_time", table_name="traffic_observations")
    op.drop_index("ix_traffic_observations_timestamp", table_name="traffic_observations")
    op.drop_index("ix_traffic_observations_point_id", table_name="traffic_observations")
    op.drop_table("traffic_observations")
