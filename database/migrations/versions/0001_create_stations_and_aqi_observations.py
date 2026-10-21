"""Create stations and aqi_observations tables for CongestAir historical pipeline.

Revision ID: 0001_create_stations_and_aqi_observations
Revises: 
Create Date: 2026-10-21 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0001_create_stations_and_aqi_observations"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create stations table
    op.create_table(
        "stations",
        sa.Column("station_id", sa.String(length=64), primary_key=True, nullable=False),
        sa.Column("station_name", sa.String(length=255), nullable=False),
        sa.Column("city", sa.String(length=100), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_stations_station_id", "stations", ["station_id"], unique=False)

    # Create aqi_observations table
    op.create_table(
        "aqi_observations",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True, nullable=False),
        sa.Column("station_id", sa.String(length=64), sa.ForeignKey("stations.station_id", ondelete="CASCADE"), nullable=False),
        sa.Column("observation_date", sa.Date(), nullable=False),
        sa.Column("aqi", sa.Float(), nullable=True),
        sa.Column("pm25", sa.Float(), nullable=True),
        sa.Column("pm10", sa.Float(), nullable=True),
        sa.Column("no2", sa.Float(), nullable=True),
        sa.Column("co", sa.Float(), nullable=True),
        sa.Column("so2", sa.Float(), nullable=True),
        sa.Column("o3", sa.Float(), nullable=True),
        sa.Column("dominant_pollutant", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("station_id", "observation_date", name="uq_station_observation_date"),
    )
    op.create_index("ix_aqi_observations_station_id", "aqi_observations", ["station_id"], unique=False)
    op.create_index("ix_aqi_observations_observation_date", "aqi_observations", ["observation_date"], unique=False)
    op.create_index("ix_aqi_obs_station_date", "aqi_observations", ["station_id", "observation_date"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_aqi_obs_station_date", table_name="aqi_observations")
    op.drop_index("ix_aqi_observations_observation_date", table_name="aqi_observations")
    op.drop_index("ix_aqi_observations_station_id", table_name="aqi_observations")
    op.drop_table("aqi_observations")

    op.drop_index("ix_stations_station_id", table_name="stations")
    op.drop_table("stations")
