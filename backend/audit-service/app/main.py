# backend/audit-service/app/main.py
import os
import uuid
import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, Depends, Header, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from shared.database import get_db
from shared.models import AuditLog, User

app = FastAPI(title="Audit Service")

class LogEntry(BaseModel):
    actor_id: uuid.UUID
    action_type: str
    entity_type: str
    entity_id: uuid.UUID
    metadata: Optional[dict] = None

async def get_current_admin(authorization: str = Header(...), db: AsyncSession = Depends(get_db)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token")
    
    token = authorization.split(" ")[1]
    try:
        import jwt # type: ignore
        secret = os.getenv("JWT_SECRET", "supersecretkey")
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        user_id = payload.get("sub")
        role = payload.get("role")
        
        if role != "platform_admin":
             raise HTTPException(status_code=403, detail="Not authorized")
             
        return user_id
    except Exception:
         raise HTTPException(status_code=401, detail="Invalid token")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/internal/log")
async def create_log(payload: LogEntry, db: AsyncSession = Depends(get_db)):
    # In production, check for internal service header/token
    # if request.headers.get("X-Internal-Service") != os.getenv("INTERNAL_TOKEN"):
    #     raise HTTPException(status_code=403, detail="Forbidden")

    log = AuditLog(
        actor_id=payload.actor_id,
        action_type=payload.action_type,
        entity_type=payload.entity_type,
        entity_id=payload.entity_id,
        log_metadata=payload.metadata
    )
    db.add(log)
    await db.commit()
    return {"status": "logged"}

@app.get("/logs")
async def get_logs(
    actor_id: Optional[uuid.UUID] = None,
    entity_type: Optional[str] = None,
    action_type: Optional[str] = None,
    admin_id: str = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    query = select(AuditLog)
    if actor_id:
        query = query.where(AuditLog.actor_id == actor_id)
    if entity_type:
        query = query.where(AuditLog.entity_type == entity_type)
    if action_type:
        query = query.where(AuditLog.action_type == action_type)
    
    query = query.order_by(AuditLog.timestamp.desc()).limit(100)
    result = await db.execute(query)
    return result.scalars().all()
