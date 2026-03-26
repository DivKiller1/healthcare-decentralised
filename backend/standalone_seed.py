# backend/standalone_seed.py
import uuid
from sqlalchemy import create_engine, Column, String, Text, Numeric, Integer, ForeignKey, DateTime, Boolean, JSON, Table, Interval, Index, CheckConstraint, select, text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

Base = declarative_base()

class Region(Base):
    __tablename__ = "regions"
    region_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    region_name = Column(Text, nullable=False, unique=True)

class User(Base):
    __tablename__ = "users"
    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(Text)
    mobile = Column(String(15), nullable=False, unique=True)
    address = Column(Text)
    role = Column(String(20), nullable=False)
    region_id = Column(UUID(as_uuid=True), ForeignKey("regions.region_id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Facility(Base):
    __tablename__ = "facilities"
    facility_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(Text, nullable=False)
    facility_type = Column(String(20), nullable=False)
    address = Column(Text, nullable=False)
    latitude = Column(Numeric(10, 7), nullable=False)
    longitude = Column(Numeric(10, 7), nullable=False)
    contact_number = Column(String(15), nullable=False)
    verification_status = Column(String(10), nullable=False, server_default="pending")
    region_id = Column(UUID(as_uuid=True), ForeignKey("regions.region_id"), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Service(Base):
    __tablename__ = "services"
    service_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    service_name = Column(Text, nullable=False)
    category = Column(Text, nullable=False)

class FacilityService(Base):
    __tablename__ = "facility_services"
    facility_id = Column(UUID(as_uuid=True), ForeignKey("facilities.facility_id", ondelete="CASCADE"), primary_key=True)
    service_id = Column(UUID(as_uuid=True), ForeignKey("services.service_id", ondelete="CASCADE"), primary_key=True)

class Request(Base):
    __tablename__ = "requests"
    request_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    service_id = Column(UUID(as_uuid=True), ForeignKey("services.service_id"), nullable=False)
    category = Column(Text, nullable=False)
    latitude = Column(Numeric(10, 7), nullable=False)
    longitude = Column(Numeric(10, 7), nullable=False)
    contact_number = Column(String(15), nullable=False)
    status = Column(String(10), nullable=False, server_default="active")
    region_id = Column(UUID(as_uuid=True), ForeignKey("regions.region_id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    # Corrected Interval syntax
    expires_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now() + interval '14 days'"))

class RoutePlan(Base):
    __tablename__ = "route_plans"
    route_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    category = Column(Text, nullable=False)
    start_lat = Column(Numeric(10, 7), nullable=False)
    start_lng = Column(Numeric(10, 7), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class RoutePlanNode(Base):
    __tablename__ = "route_plan_nodes"
    route_id = Column(UUID(as_uuid=True), ForeignKey("route_plans.route_id", ondelete="CASCADE"), primary_key=True)
    request_id = Column(UUID(as_uuid=True), ForeignKey("requests.request_id"), primary_key=True)
    visit_order = Column(Integer, nullable=False)

class MetricsSnapshot(Base):
    __tablename__ = "metrics_snapshots"
    metric_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    metric_type = Column(String(30), nullable=False)
    metric_value = Column(JSON, nullable=False)
    calculated_at = Column(DateTime(timezone=True), server_default=func.now())

class AuditLog(Base):
    __tablename__ = "audit_logs"
    log_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    actor_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    action_type = Column(Text, nullable=False)
    entity_type = Column(Text, nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    log_metadata = Column(JSON)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

# Sync initialization
SYNC_URL = "postgresql://user:password@localhost:5432/healthcare_db"
engine = create_engine(SYNC_URL)
Session = sessionmaker(bind=engine)

def main():
    Base.metadata.create_all(engine)
    print("Tables created.")
    
    session = Session()
    # Region
    rid = uuid.uuid4()
    if not session.query(Region).filter_by(region_name="Dehradun").first():
        session.add(Region(region_id=rid, region_name="Dehradun"))
        print("Region added.")
    
    # Services
    if not session.query(Service).filter_by(service_name="Polio Vaccination").first():
        session.add(Service(service_name="Polio Vaccination", category="vaccination"))
        session.add(Service(service_name="TB Screening", category="screening"))
        session.add(Service(service_name="Blood Donation", category="emergency"))
        print("Services added.")

    # Clinic User for testing
    if not session.query(User).filter_by(mobile="9000000000").first():
        session.add(User(
            user_id=uuid.uuid4(),
            name="Test Clinic",
            mobile="9000000000",
            role="clinic",
            region_id=rid
        ))
        print("Clinic user added.")
    
    session.commit()
    session.close()
    print("Seeding done.")

if __name__ == "__main__":
    main()
