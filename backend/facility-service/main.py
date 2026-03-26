from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import psycopg2
import os
from datetime import datetime
from auth_middleware import verify_token

app = FastAPI(title="Facility Service v2.0")

# =========================
# CORS
# =========================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# DB CONFIG
# =========================
DB_HOST = os.getenv("DB_HOST", "postgres")
DB_NAME = os.getenv("POSTGRES_DB", "usersdb")
DB_USER = os.getenv("POSTGRES_USER", "useradmin")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "userpass")

def get_conn():
    return psycopg2.connect(
        host=DB_HOST,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )

# =========================
# MODELS
# =========================
class Facility(BaseModel):
    name: str
    address: str
    mobile_number: str
    category: str
    region: str
    lat: float
    lon: float

# =========================
# STARTUP
# =========================
@app.on_event("startup")
def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS facilities (
        id SERIAL PRIMARY KEY,
        name TEXT,
        address TEXT,
        mobile TEXT,
        category TEXT,
        region TEXT,
        lat FLOAT,
        lon FLOAT,
        status TEXT DEFAULT 'PENDING',
        created_at TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()

# =========================
# HEALTH
# =========================
@app.get("/health")
def health():
    return {
        "status": "facility-service-up",
        "version": "2.0",
        "jwt_protected": True
    }

# =========================
# REGISTER FACILITY (JWT Required)
# =========================
@app.post("/facility/register")
def register_facility(
    facility: Facility,
    user=Depends(verify_token)
):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO facilities (
        name, address, mobile,
        category, region,
        lat, lon,
        status, created_at
    )
    VALUES (%s,%s,%s,%s,%s,%s,%s,'PENDING',%s)
    """, (
        facility.name,
        facility.address,
        facility.mobile_number,
        facility.category,
        facility.region,
        facility.lat,
        facility.lon,
        datetime.utcnow()
    ))

    conn.commit()
    conn.close()

    return {
        "message": "Facility registered",
        "status": "PENDING",
        "submitted_by": user.get("mobile")
    }

# =========================
# PUBLIC FACILITIES (OPEN)
# =========================
@app.get("/facility/public")
def list_public_facilities():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    SELECT name, address, mobile,
           category, region,
           lat, lon
    FROM facilities
    WHERE status='APPROVED'
    """)

    rows = cur.fetchall()
    conn.close()

    return [
        {
            "name": r[0],
            "address": r[1],
            "mobile": r[2],
            "category": r[3],
            "region": r[4],
            "lat": r[5],
            "lon": r[6]
        }
        for r in rows
    ]

# =========================
# APPROVE FACILITY (Govt Only)
# =========================
@app.post("/facility/approve/{facility_id}")
def approve_facility(
    facility_id: int,
    user=Depends(verify_token)
):
    # Role enforcement
    if user.get("role") != "govt":
        raise HTTPException(status_code=403, detail="Only govt can approve facilities")

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    UPDATE facilities
    SET status='APPROVED'
    WHERE id=%s
    """, (facility_id,))

    conn.commit()
    conn.close()

    return {
        "message": "Facility approved",
        "approved_by": user.get("mobile")
    }

# =========================
# LIST ALL FACILITIES (Govt)
# =========================
@app.get("/facility/all")
def list_all_facilities(user=Depends(verify_token)):
    if user.get("role") != "govt":
        raise HTTPException(status_code=403, detail="Access denied")

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    SELECT id, name, category,
           region, status, created_at
    FROM facilities
    ORDER BY created_at DESC
    """)

    rows = cur.fetchall()
    conn.close()

    return [
        {
            "id": r[0],
            "name": r[1],
            "category": r[2],
            "region": r[3],
            "status": r[4],
            "created_at": str(r[5])
        }
        for r in rows
    ]