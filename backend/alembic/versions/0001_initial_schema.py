"""initial schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-10-30

Creates the full healthcare multi-portal schema as defined in
shared/models.py: regions, services, users, facilities, facility_services,
requests, route_plans, route_plan_nodes, metrics_snapshots and audit_logs.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "0001_initial_schema"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "regions",
        sa.Column("region_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("region_name", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("region_id"),
        sa.UniqueConstraint("region_name"),
    )

    op.create_table(
        "services",
        sa.Column("service_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("service_name", sa.Text(), nullable=False),
        sa.Column("category", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("service_id"),
    )

    op.create_table(
        "users",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.Text(), nullable=True),
        sa.Column("mobile", sa.String(length=15), nullable=False),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("region_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.CheckConstraint(
            "role IN ('citizen', 'clinic', 'govt_employee', 'govt_admin', 'platform_admin')"
        ),
        sa.ForeignKeyConstraint(["region_id"], ["regions.region_id"]),
        sa.PrimaryKeyConstraint("user_id"),
        sa.UniqueConstraint("mobile"),
    )

    op.create_table(
        "facilities",
        sa.Column("facility_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("facility_type", sa.String(length=20), nullable=False),
        sa.Column("address", sa.Text(), nullable=False),
        sa.Column("latitude", sa.Numeric(precision=10, scale=7), nullable=False),
        sa.Column("longitude", sa.Numeric(precision=10, scale=7), nullable=False),
        sa.Column("contact_number", sa.String(length=15), nullable=False),
        sa.Column("verification_status", sa.String(length=10), server_default="pending", nullable=False),
        sa.Column("region_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.CheckConstraint(
            "facility_type IN ('hospital', 'clinic', 'blood_bank', 'diagnostic')"
        ),
        sa.CheckConstraint(
            "verification_status IN ('pending', 'approved', 'rejected')"
        ),
        sa.ForeignKeyConstraint(["region_id"], ["regions.region_id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.user_id"]),
        sa.PrimaryKeyConstraint("facility_id"),
    )

    op.create_table(
        "facility_services",
        sa.Column("facility_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("service_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["facility_id"], ["facilities.facility_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["service_id"], ["services.service_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("facility_id", "service_id"),
    )

    op.create_table(
        "requests",
        sa.Column("request_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("service_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("category", sa.Text(), nullable=False),
        sa.Column("latitude", sa.Numeric(precision=10, scale=7), nullable=False),
        sa.Column("longitude", sa.Numeric(precision=10, scale=7), nullable=False),
        sa.Column("contact_number", sa.String(length=15), nullable=False),
        sa.Column("status", sa.String(length=10), server_default="active", nullable=False),
        sa.Column("region_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column(
            "expires_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now() + interval '14 days'"),
            nullable=False,
        ),
        sa.CheckConstraint("status IN ('active', 'closed', 'expired')"),
        sa.ForeignKeyConstraint(["created_by"], ["users.user_id"]),
        sa.ForeignKeyConstraint(["service_id"], ["services.service_id"]),
        sa.ForeignKeyConstraint(["region_id"], ["regions.region_id"]),
        sa.PrimaryKeyConstraint("request_id"),
    )
    op.create_index("idx_requests_region_status", "requests", ["region_id", "status"])

    op.create_table(
        "route_plans",
        sa.Column("route_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("category", sa.Text(), nullable=False),
        sa.Column("start_lat", sa.Numeric(precision=10, scale=7), nullable=False),
        sa.Column("start_lng", sa.Numeric(precision=10, scale=7), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["created_by"], ["users.user_id"]),
        sa.PrimaryKeyConstraint("route_id"),
    )

    op.create_table(
        "route_plan_nodes",
        sa.Column("route_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("request_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("visit_order", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["route_id"], ["route_plans.route_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["request_id"], ["requests.request_id"]),
        sa.PrimaryKeyConstraint("route_id", "request_id"),
    )

    op.create_table(
        "metrics_snapshots",
        sa.Column("metric_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("metric_type", sa.String(length=30), nullable=False),
        sa.Column("metric_value", sa.JSON(), nullable=False),
        sa.Column("calculated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.CheckConstraint(
            "metric_type IN ('cloud_savings', 'demand_cluster', 'efficiency')"
        ),
        sa.PrimaryKeyConstraint("metric_id"),
    )

    op.create_table(
        "audit_logs",
        sa.Column("log_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("action_type", sa.Text(), nullable=False),
        sa.Column("entity_type", sa.Text(), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("log_metadata", sa.JSON(), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["actor_id"], ["users.user_id"]),
        sa.PrimaryKeyConstraint("log_id"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("audit_logs")
    op.drop_table("metrics_snapshots")
    op.drop_table("route_plan_nodes")
    op.drop_table("route_plans")
    op.drop_index("idx_requests_region_status", table_name="requests")
    op.drop_table("requests")
    op.drop_table("facility_services")
    op.drop_table("facilities")
    op.drop_table("users")
    op.drop_table("services")
    op.drop_table("regions")
