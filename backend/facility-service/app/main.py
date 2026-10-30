# backend/facility-service/app/main.py
import os
import uuid
from typing import Optional, List

from fastapi import FastAPI, HTTPException, Depends, Header, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from shared.database import get_db
from shared.models import User, Facility, Service, FacilityService
from shared.utils import log_event

app = FastAPI(title="Facility Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class FacilityCreate(BaseModel):
    name: str
    facility_type: str
    address: str
    latitude: float
    longitude: float
    contact_number: str
    region_id: uuid.UUID

class VerifyRequest(BaseModel):
    status: str # approved, rejected
    note: Optional[str] = None

async def get_current_user(authorization: str = Header(...), db: AsyncSession = Depends(get_db)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token")
    
    token = authorization.split(" ")[1]
    import jwt # type: ignore
    secret = os.getenv("JWT_SECRET", "supersecretkey")
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        user_id = payload.get("sub")
        role = payload.get("role")
        result = await db.execute(select(User).where(User.user_id == uuid.UUID(user_id)))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/")
async def list_verified_facilities(
    region_id: Optional[uuid.UUID] = None,
    facility_type: Optional[str] = Query(None, alias="type"),
    service_id: Optional[uuid.UUID] = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(Facility).where(Facility.verification_status == "approved")
    if region_id:
        query = query.where(Facility.region_id == region_id)
    if facility_type:
        query = query.where(Facility.facility_type == facility_type)
    
    if service_id:
        query = query.join(FacilityService).where(FacilityService.service_id == service_id)
    
    result = await db.execute(query)
    return result.scalars().all()

@app.get("/{facility_id}")
async def get_facility_detail(facility_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Facility).where(Facility.facility_id == facility_id))
    facility = result.scalar_one_or_none()
    if not facility:
        raise HTTPException(status_code=404, detail="Facility not found")
    # For public endpoint, we only show approved facilities or if user is owner/govt
    # But spec says "GET /:facility_id → facility detail [public]"
    # It doesn't explicitly restrict to approved here, but usually it should.
    # I'll stick to the spec "public".
    return facility

@app.get("/pending")
async def list_pending(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if current_user.role != "govt_admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    result = await db.execute(select(Facility).where(Facility.verification_status == "pending"))
    return result.scalars().all()

@app.post("/")
async def register_facility(payload: FacilityCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if current_user.role != "clinic":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    new_facility = Facility(
        name=payload.name,
        facility_type=payload.facility_type,
        address=payload.address,
        latitude=payload.latitude,
        longitude=payload.longitude,
        contact_number=payload.contact_number,
        region_id=payload.region_id,
        created_by=current_user.user_id,
        verification_status="pending"
    )
    db.add(new_facility)
    await db.commit()
    await db.refresh(new_facility)
    
    await log_event(
        actor_id=current_user.user_id,
        action_type="FACILITY_REGISTERED",
        entity_type="facility",
        entity_id=new_facility.facility_id
    )
    
    return new_facility

@app.put("/{facility_id}/verify")
async def verify_facility(facility_id: uuid.UUID, payload: VerifyRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if current_user.role != "govt_admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    if payload.status not in ["approved", "rejected"]:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    result = await db.execute(select(Facility).where(Facility.facility_id == facility_id))
    facility = result.scalar_one_or_none()
    if not facility:
        raise HTTPException(status_code=404, detail="Facility not found")
    
    facility.verification_status = payload.status
    await db.commit()
    
    await log_event(
        actor_id=current_user.user_id,
        action_type=f"FACILITY_{payload.status.upper()}",
        entity_type="facility",
        entity_id=facility.facility_id
    )
    
    return {"status": payload.status}

@app.post("/{facility_id}/services")
async def update_services(facility_id: uuid.UUID, service_ids: List[uuid.UUID], current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Facility).where(Facility.facility_id == facility_id))
    facility = result.scalar_one_or_none()
    
    if not facility or (facility.created_by != current_user.user_id and current_user.role != "govt_admin"):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Remove existing services
    await db.execute(FacilityService.__table__.delete().where(FacilityService.facility_id == facility_id))
    
    # Add new ones
    for s_id in service_ids:
        db.add(FacilityService(facility_id=facility_id, service_id=s_id))
    
    await db.commit()
    return {"message": "Services updated"}
