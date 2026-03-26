# backend/seed.py
import asyncio
import uuid
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from shared.models import Region, Service, Base
from shared.database import DATABASE_URL

engine = create_async_engine(DATABASE_URL)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def init_db():
    async with engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
    print("Database schema created successfully.")

async def seed():
    async with AsyncSessionLocal() as db:
        try:
            # Check if region exists
            res = await db.execute(select(Region).where(Region.region_name == "Dehradun"))
            region = res.scalar_one_or_none()
            if not region:
                region = Region(region_id=uuid.uuid4(), region_name="Dehradun")
                db.add(region)
                await db.flush()
                print("Created region: Dehradun")
            else:
                print("Region Dehradun already exists.")
            
            # Check if services exist
            for s_name, cat in [("Polio Vaccination", "vaccination"), ("TB Screening", "screening"), ("Blood Donation", "emergency")]:
                res = await db.execute(select(Service).where(Service.service_name == s_name))
                if not res.scalar_one_or_none():
                    db.add(Service(service_name=s_name, category=cat))
                    print(f"Created service: {s_name}")
            
            await db.commit()
            print("Database seeding completed.")
        except Exception as e:
            print(f"Seeding failed: {e}")
            await db.rollback()

async def main():
    await init_db()
    await seed()

if __name__ == "__main__":
    asyncio.run(main())
