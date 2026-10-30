# backend/govt-ops-service/app/main.py
import os
import uuid
from typing import Optional

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from shared.database import get_db
from shared.models import User, Request as ServiceRequest, RoutePlan, RoutePlanNode

app = FastAPI(title="Govt Ops Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ROUTING_SERVICE_URL = os.getenv("ROUTING_SERVICE_URL", "http://routing-svc")

class RouteTriggerRequest(BaseModel):
    category: str
    start_lat: float
    start_lng: float

async def get_current_user(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token")
    
    token = authorization.split(" ")[1]
    import jwt # type: ignore
    secret = os.getenv("JWT_SECRET", "supersecretkey")
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        if payload.get("role") not in ["govt_employee", "govt_admin"]:
            raise HTTPException(status_code=403, detail="Not authorized")
        return payload
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/requests/summary")
async def get_summary(user_data: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    region_id = uuid.UUID(user_data["region_id"])
    
    result = await db.execute(
        select(ServiceRequest.category, func.count(ServiceRequest.request_id))
        .where(ServiceRequest.region_id == region_id, ServiceRequest.status == "active")
        .group_by(ServiceRequest.category)
    )
    summary = {row[0]: row[1] for row in result.all()}
    return summary

@app.get("/requests/map")
async def get_map_data(user_data: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    region_id = uuid.UUID(user_data["region_id"])
    result = await db.execute(
        select(ServiceRequest.latitude, ServiceRequest.longitude, ServiceRequest.request_id, ServiceRequest.category)
        .where(ServiceRequest.region_id == region_id, ServiceRequest.status == "active")
    )
    return result.all()

@app.post("/routes")
async def trigger_route(payload: RouteTriggerRequest, user_data: dict = Depends(get_current_user)):
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{ROUTING_SERVICE_URL}/generate", json={
            "govt_user_id": user_data["sub"],
            "category": payload.category,
            "region_id": user_data["region_id"],
            "start_lat": payload.start_lat,
            "start_lng": payload.start_lng
        })
        if resp.status_code != 200:
             raise HTTPException(status_code=resp.status_code, detail=resp.text)
        return resp.json()

@app.get("/routes")
async def list_routes(user_data: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(RoutePlan).where(RoutePlan.created_by == uuid.UUID(user_data["sub"])))
    return result.scalars().all()

@app.get("/routes/{route_id}")
async def get_route_detail(route_id: uuid.UUID, user_data: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(RoutePlanNode, ServiceRequest)
        .join(ServiceRequest, RoutePlanNode.request_id == ServiceRequest.request_id)
        .where(RoutePlanNode.route_id == route_id)
        .order_by(RoutePlanNode.visit_order)
    )
    nodes = []
    for node, req in result.all():
         nodes.append({
             "request_id": str(req.request_id),
             "latitude": req.latitude,
             "longitude": req.longitude,
             "visit_order": node.visit_order
         })
    return nodes
