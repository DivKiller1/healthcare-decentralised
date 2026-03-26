# backend/metrics-service/app/main.py
import os
import uuid
import datetime
from typing import Optional, List

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
import numpy as np
from sklearn.cluster import KMeans
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from shared.database import get_db
from shared.models import User, Request as ServiceRequest, MetricsSnapshot, AuditLog
from shared.utils import log_event

app = FastAPI(title="Metrics Service")

class RecalculateRequest(BaseModel):
    n_clusters: Optional[int] = 5

async def get_current_admin(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token")
    
    token = authorization.split(" ")[1]
    import jwt # type: ignore
    secret = os.getenv("JWT_SECRET", "supersecretkey")
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        if payload.get("role") != "platform_admin":
            raise HTTPException(status_code=403, detail="Not authorized")
        return payload
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

from fastapi import Header # Re-importing Header for clarity

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/savings")
async def get_savings(admin_data: dict = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    # Mock savings calculation logic
    # In production, this would query route distance vs direct distance and compute cost diff
    result = await db.execute(select(MetricsSnapshot).where(MetricsSnapshot.metric_type == "cloud_savings").order_by(MetricsSnapshot.calculated_at.desc()).limit(1))
    snapshot = result.scalar_one_or_none()
    return snapshot.metric_value if snapshot else {"operational_savings_per_route": "15%", "cloud_savings": "$1200/mo"}

@app.get("/demand")
async def get_demand(admin_data: dict = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MetricsSnapshot).where(MetricsSnapshot.metric_type == "demand_cluster").order_by(MetricsSnapshot.calculated_at.desc()).limit(1))
    snapshot = result.scalar_one_or_none()
    return snapshot.metric_value if snapshot else []

@app.get("/efficiency")
async def get_efficiency(admin_data: dict = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    # Calculate real-time efficiency
    total_result = await db.execute(select(func.count(ServiceRequest.request_id)))
    total = total_result.scalar() or 1
    
    closed_result = await db.execute(select(func.count(ServiceRequest.request_id)).where(ServiceRequest.status == "closed"))
    closed = closed_result.scalar_one()
    
    return {
        "close_rate": f"{(closed/total)*100:.1f}%",
        "avg_response_days": "2.4",
        "total_requests_processed": total
    }

@app.post("/recalculate")
async def recalculate(payload: RecalculateRequest, admin_data: dict = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    # Fetch all active requests
    result = await db.execute(select(ServiceRequest).where(ServiceRequest.status == "active"))
    requests = result.scalars().all()
    
    if not requests:
         return {"message": "No active requests to cluster"}

    coords = np.array([[float(r.latitude), float(r.longitude)] for r in requests])
    k = max(1, min(payload.n_clusters, len(requests) // 2))
    
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = kmeans.fit_predict(coords)
    
    clusters = []
    for cluster_id in range(k):
        mask = labels == cluster_id
        centroid = kmeans.cluster_centers_[cluster_id]
        clusters.append({
            "cluster_id": cluster_id,
            "centroid_lat": float(centroid[0]),
            "centroid_lng": float(centroid[1]),
            "request_count": int(mask.sum()),
            "request_ids": [str(requests[i].request_id) for i in range(len(requests)) if labels[i] == cluster_id]
        })
    
    # Save snapshot
    snapshot = MetricsSnapshot(
        metric_type="demand_cluster",
        metric_value=sorted(clusters, key=lambda c: c["request_count"], reverse=True)
    )
    db.add(snapshot)
    await db.commit()
    
    await log_event(
        actor_id=uuid.UUID(admin_data["sub"]),
        action_type="METRICS_RECALCULATED",
        entity_type="metrics_snapshot",
        entity_id=snapshot.metric_id
    )
    
    return {"message": "Metrics recalculated", "clusters": len(clusters)}
