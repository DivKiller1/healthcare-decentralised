# backend/seed_sync.py
import uuid
import sqlalchemy
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from shared.models import Region, Service, Base

# Use sync engine URL for seeding
SYNC_DATABASE_URL = "postgresql://user:password@localhost:5432/healthcare_db"

engine = create_engine(SYNC_DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def init_db():
    Base.metadata.create_all(engine)
    print("Database schema created successfully (Sync).")

def seed():
    session = SessionLocal()
    try:
        # Check if region exists
        res = session.execute(select(Region).where(Region.region_name == "Dehradun"))
        region = res.scalar_one_or_none()
        if not region:
            new_id = uuid.uuid4()
            region = Region(region_id=new_id, region_name="Dehradun")
            session.add(region)
            session.flush()
            print(f"Created region: Dehradun ({new_id})")
        else:
            print("Region Dehradun already exists.")
        
        # Check if services exist
        for s_name, cat in [("Polio Vaccination", "vaccination"), ("TB Screening", "screening"), ("Blood Donation", "emergency")]:
            res = session.execute(select(Service).where(Service.service_name == s_name))
            if not res.scalar_one_or_none():
                session.add(Service(service_name=s_name, category=cat))
                print(f"Created service: {s_name}")
        
        session.commit()
        print("Database seeding completed.")
    except Exception as e:
        print(f"Seeding failed: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    init_db()
    seed()
