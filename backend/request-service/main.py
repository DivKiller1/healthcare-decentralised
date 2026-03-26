from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from auth_middleware import verify_token
import psycopg2
import os
from datetime import datetime, timedelta

app = FastAPI(title="Request Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# Database Configuration
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
# Models
# =========================
class RequestCreate(BaseModel):
    category: str
    address: str
    region: str
    description: str


class AssignRequest(BaseModel):
    assigned_to: str


# =========================
# Priority Logic
# =========================
def get_priority(category: str) -> int:
    mapping = {
        "blood": 1,
        "emergency": 1,
        "polio": 2,
        "clinic": 3
    }
    return mapping.get(category.lower(), 3)


# =========================
# Startup
# =========================
@app.on_event("startup")
def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS requests (
        id SERIAL PRIMARY KEY,
        category TEXT,
        address TEXT,
        region TEXT,
        description TEXT,
        status TEXT DEFAULT 'OPEN',
        priority INT DEFAULT 3,
        assigned_to TEXT,
        created_at TIMESTAMP,
        expires_at TIMESTAMP
    )
    """)
    conn.commit()
    conn.close()


# =========================
# Health
# =========================
@app.get("/health")
def health():
    return {"status": "ok", "service": "request"}


# =========================
# Create Request (Citizen Only)
# =========================
@app.post("/request/create")
def create_request(
    req: RequestCreate,
    user=Depends(verify_token)
):
    if user["role"] != "citizen":
        raise HTTPException(status_code=403, detail="Only citizens can create requests")

    now = datetime.utcnow()
    expires = now + timedelta(days=14)
    priority = get_priority(req.category)

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO requests
    (category, address, region, description, status, priority, created_at, expires_at)
    VALUES (%s, %s, %s, %s, 'OPEN', %s, %s, %s)
    RETURNING id
    """, (
        req.category,
        req.address,
        req.region,
        req.description,
        priority,
        now,
        expires
    ))

    req_id = cur.fetchone()[0]
    conn.commit()
    conn.close()

    return {
        "id": req_id,
        "status": "OPEN",
        "priority": priority,
        "expires_at": str(expires)
    }


# =========================
# Public Open Requests (No Auth)
# =========================
@app.get("/request/open")
def list_open_requests(category: str = None):
    conn = get_conn()
    cur = conn.cursor()

    if category:
        cur.execute("""
        SELECT id, category, address, region, description, priority, assigned_to
        FROM requests
        WHERE status='OPEN'
        AND expires_at > NOW()
        AND category=%s
        ORDER BY priority ASC, created_at ASC
        """, (category,))
    else:
        cur.execute("""
        SELECT id, category, address, region, description, priority, assigned_to
        FROM requests
        WHERE status='OPEN'
        AND expires_at > NOW()
        ORDER BY priority ASC, created_at ASC
        """)

    rows = cur.fetchall()
    conn.close()

    return [
        {
            "id": r[0],
            "category": r[1],
            "address": r[2],
            "region": r[3],
            "description": r[4],
            "priority": r[5],
            "assigned_to": r[6]
        }
        for r in rows
    ]


# =========================
# Assign Request (Government/Admin)
# =========================
@app.post("/request/assign/{req_id}")
def assign_request(
    req_id: int,
    body: AssignRequest,
    user=Depends(verify_token)
):
    if user["role"] not in ["government", "admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    UPDATE requests
    SET status='ASSIGNED',
        assigned_to=%s
    WHERE id=%s
    """, (body.assigned_to, req_id))

    conn.commit()
    conn.close()

    return {"id": req_id, "status": "ASSIGNED"}


# =========================
# Mark Enroute (Govt/Admin)
# =========================
@app.post("/request/enroute/{req_id}")
def mark_enroute(req_id: int, user=Depends(verify_token)):
    if user["role"] not in ["government", "admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    UPDATE requests
    SET status='ENROUTE'
    WHERE id=%s
    """, (req_id,))

    conn.commit()
    conn.close()

    return {"id": req_id, "status": "ENROUTE"}


# =========================
# Close Request (Govt/Admin)
# =========================
@app.post("/request/close/{req_id}")
def close_request(req_id: int, user=Depends(verify_token)):
    if user["role"] not in ["government", "admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    UPDATE requests
    SET status='CLOSED'
    WHERE id=%s
    """, (req_id,))

    conn.commit()
    conn.close()

    return {"id": req_id, "status": "CLOSED"}


# =========================
# Government Dashboard View (Protected)
# =========================
@app.get("/govt/requests")
def govt_list_requests(
    status: str = None,
    category: str = None,
    user=Depends(verify_token)
):
    if user["role"] not in ["government", "admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    conn = get_conn()
    cur = conn.cursor()

    query = """
        SELECT id, category, address, region, description,
               status, priority, assigned_to, created_at, expires_at
        FROM requests
        WHERE 1=1
    """
    params = []

    if status:
        query += " AND status=%s"
        params.append(status)

    if category:
        query += " AND category=%s"
        params.append(category)

    query += " ORDER BY priority ASC, created_at ASC"

    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()

    return [
        {
            "id": r[0],
            "category": r[1],
            "address": r[2],
            "region": r[3],
            "description": r[4],
            "status": r[5],
            "priority": r[6],
            "assigned_to": r[7],
            "created_at": str(r[8]),
            "expires_at": str(r[9])
        }
        for r in rows
    ]


# =========================
# Admin Metrics (Protected)
# =========================
@app.get("/request/metrics")
def metrics(user=Depends(verify_token)):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM requests")
    total = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM requests WHERE status='OPEN'")
    open_count = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM requests WHERE status='CLOSED'")
    closed_count = cur.fetchone()[0]

    conn.close()

    return {
        "total_requests": total,
        "open_requests": open_count,
        "closed_requests": closed_count
    }