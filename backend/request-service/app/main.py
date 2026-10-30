# backend/request-service/app/main.py
import os
import uuid
import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from shared.database import get_db, AsyncSessionLocal
from shared.models import User, Request as ServiceRequest, Service
from shared.utils import log_event

app = FastAPI(title="Request Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

scheduler = AsyncIOScheduler()

class RequestCreate(BaseModel):
    service_id: uuid.UUID
    latitude: float
    longitude: float
    contact_number: str

async def get_current_user(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token")
    
    token = authorization.split(" ")[1]
    import jwt # type: ignore
    secret = os.getenv("JWT_SECRET", "supersecretkey")
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        return payload
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/")
async def create_request(payload: RequestCreate, user_data: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if user_data.get("role") not in ["citizen", "clinic"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Fetch service to get category
    srv_result = await db.execute(select(Service).where(Service.service_id == payload.service_id))
    service = srv_result.scalar_one_or_none()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    new_request = ServiceRequest(
        created_by=uuid.UUID(user_data["sub"]),
        service_id=payload.service_id,
        category=service.category,
        latitude=payload.latitude,
        longitude=payload.longitude,
        contact_number=payload.contact_number,
        region_id=uuid.UUID(user_data["region_id"]),
        status="active"
    )
    db.add(new_request)
    await db.commit()
    await db.refresh(new_request)
    
    await log_event(
        actor_id=uuid.UUID(user_data["sub"]),
        action_type="REQUEST_CREATED",
        entity_type="request",
        entity_id=new_request.request_id
    )
    
    return new_request

@app.get("/mine")
async def get_mine(user_data: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ServiceRequest).where(ServiceRequest.created_by == uuid.UUID(user_data["sub"])))
    return result.scalars().all()

@app.get("/region")
async def get_region_requests(category: Optional[str] = None, user_data: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if user_data.get("role") not in ["govt_employee", "govt_admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    query = select(ServiceRequest).where(ServiceRequest.region_id == uuid.UUID(user_data["region_id"]), ServiceRequest.status == "active")
    if category:
        query = query.where(ServiceRequest.category == category)
    
    result = await db.execute(query)
    return result.scalars().all()

@app.get("/{request_id}")
async def get_request_detail(request_id: uuid.UUID, user_data: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ServiceRequest).where(ServiceRequest.request_id == request_id))
    request = result.scalar_one_or_none()
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    # Check owner or govt role
    is_owner = str(request.created_by) == user_data["sub"]
    is_govt = user_data["role"] in ["govt_employee", "govt_admin"]
    
    if not is_owner and not is_govt:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    return request

@app.delete("/{request_id}/close")
async def close_request(request_id: uuid.UUID, user_data: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if user_data.get("role") not in ["govt_employee", "govt_admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    await db.execute(update(ServiceRequest).where(ServiceRequest.request_id == request_id).values(status="closed"))
    await db.commit()
    
    await log_event(
        actor_id=uuid.UUID(user_data["sub"]),
        action_type="REQUEST_CLOSED",
        entity_type="request",
        entity_id=request_id
    )
    
    return {"status": "closed"}

# Auto-expiry job
async def expire_requests():
    async with AsyncSessionLocal() as db:
        await db.execute(
            update(ServiceRequest)
            .where(ServiceRequest.status == "active", ServiceRequest.expires_at < datetime.datetime.utcnow())
            .values(status="expired")
        )
        await db.commit()

@app.on_event("startup")
async def start_scheduler():
    scheduler.add_job(expire_requests, 'interval', hours=1)
    scheduler.start()
