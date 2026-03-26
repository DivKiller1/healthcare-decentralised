# backend/user-service/app/main.py
import os
import uuid
from typing import Optional

from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from shared.database import get_db
from shared.models import User

app = FastAPI(title="User Service")

class UserUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None

async def get_current_user(authorization: str = Header(...), db: AsyncSession = Depends(get_db)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token")
    
    token = authorization.split(" ")[1]
    try:
        secret = os.getenv("JWT_SECRET", "supersecretkey")
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        result = await db.execute(select(User).where(User.user_id == uuid.UUID(user_id)))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/me")
async def get_me(user: User = Depends(get_current_user)):
    return {
        "user_id": str(user.user_id),
        "name": user.name,
        "mobile": user.mobile,
        "address": user.address,
        "role": user.role,
        "region_id": str(user.region_id),
        "created_at": user.created_at
    }

@app.put("/me")
async def update_me(payload: UserUpdate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if payload.name is not None:
        user.name = payload.name
    if payload.address is not None:
        user.address = payload.address
    
    await db.commit()
    await db.refresh(user)
    return {"message": "Profile updated", "user": {"name": user.name, "address": user.address}}

# Admin endpoints (to be implemented fully later)
@app.get("/{user_id}")
async def get_user_by_id(user_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if current_user.role != "platform_admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    result = await db.execute(select(User).where(User.user_id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.get("/")
async def list_users(role: Optional[str] = None, region_id: Optional[uuid.UUID] = None, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if current_user.role != "platform_admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    query = select(User)
    if role:
        query = query.where(User.role == role)
    if region_id:
        query = query.where(User.region_id == region_id)
    
    result = await db.execute(query)
    return result.scalars().all()

import jwt # type: ignore
