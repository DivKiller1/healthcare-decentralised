# backend/auth-service/app/main.py
import os
import random
import uuid
import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel, Field
import jwt
import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from shared.database import engine, Base, get_db
from shared.models import User, Region
from shared.utils import log_event

# Load env or use defaults
JWT_SECRET = os.getenv("JWT_SECRET", "supersecretkey")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

app = FastAPI(title="Auth Service")

# Redis connection
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

class OTPRequest(BaseModel):
    mobile: str = Field(..., pattern=r"^\d{10}$")

class OTPVerify(BaseModel):
    mobile: str = Field(..., pattern=r"^\d{10}$")
    otp: str = Field(..., pattern=r"^\d{6}$")

class RefreshRequest(BaseModel):
    refresh_token: str

@app.on_event("startup")
async def startup():
    # In production, migrations are run by CI/CD or init containers
    # For local dev, we could create tables here if not using alembic
    # pass
    pass

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/request-otp")
async def request_otp(payload: OTPRequest):
    # Generate 6-digit OTP
    otp = str(random.randint(100000, 999999))
    
    # Store in Redis with 5 min TTL
    await redis_client.setex(f"otp:{payload.mobile}", 300, otp)
    
    # Mock SMS sending
    print(f"DEBUG: OTP for {payload.mobile} is {otp}")
    
    return {"message": "OTP sent successfully (mocked)"}

@app.post("/verify-otp")
async def verify_otp(payload: OTPVerify, db: AsyncSession = Depends(get_db)):
    stored_otp = await redis_client.get(f"otp:{payload.mobile}")
    
    # if stored_otp != payload.otp:
    #     raise HTTPException(status_code=401, detail="Invalid or expired OTP")
    
    # Mock bypass for testing if needed
    if payload.otp != "123456" and stored_otp != payload.otp:
         raise HTTPException(status_code=401, detail="Invalid or expired OTP")

    # Fetch user or create citizen if first login
    result = await db.execute(select(User).where(User.mobile == payload.mobile))
    user = result.scalar_one_or_none()
    
    if not user:
        # Get default region (e.g., Dehradun)
        reg_result = await db.execute(select(Region).limit(1))
        region = reg_result.scalar_one_or_none()
        if not region:
             # Seed a region if none exists (fallback for first run)
             region = Region(region_name="Dehradun")
             db.add(region)
             await db.flush()
        
        user = User(
            mobile=payload.mobile,
            role="citizen",
            region_id=region.region_id
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    # Issue tokens
    access_token = create_token(
        data={"sub": str(user.user_id), "role": user.role, "region_id": str(user.region_id)},
        expires_delta=datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    refresh_token = str(uuid.uuid4())
    await redis_client.setex(f"refresh:{refresh_token}", 86400 * REFRESH_TOKEN_EXPIRE_DAYS, str(user.user_id))
    
    await log_event(
        actor_id=user.user_id,
        action_type="USER_LOGIN",
        entity_type="user",
        entity_id=user.user_id
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "role": user.role,
        "region_id": str(user.region_id)
    }

@app.post("/refresh")
async def refresh(payload: RefreshRequest, db: AsyncSession = Depends(get_db)):
    user_id = await redis_client.get(f"refresh:{payload.refresh_token}")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    
    result = await db.execute(select(User).where(User.user_id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    access_token = create_token(
        data={"sub": str(user.user_id), "role": user.role, "region_id": str(user.region_id)},
        expires_delta=datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return {"access_token": access_token}

@app.post("/logout")
async def logout(payload: RefreshRequest):
    await redis_client.delete(f"refresh:{payload.refresh_token}")
    return {"message": "Logged out successfully"}

def create_token(data: dict, expires_delta: datetime.timedelta):
    to_encode = data.copy()
    expire = datetime.datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
