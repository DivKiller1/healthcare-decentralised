from fastapi import FastAPI
import psycopg2
import os

app = FastAPI(title="Metrics Service")

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

@app.get("/health")
def health():
    return {"status": "ok", "service": "metrics"}

@app.get("/metrics/requests")
def request_metrics():
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

@app.get("/metrics/facilities")
def facility_metrics():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM facilities")
    total = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM facilities WHERE status='APPROVED'")
    approved = cur.fetchone()[0]

    conn.close()

    return {
        "total_facilities": total,
        "approved_facilities": approved
    }

@app.get("/metrics/cloud-savings")
def cloud_savings():
    # Simple SaaS model
    BASE_COST_PER_REQUEST = 0.05  # hypothetical dollars
    OPTIMIZED_COST_PER_REQUEST = 0.02

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM requests")
    total_requests = cur.fetchone()[0]
    conn.close()

    base_cost = total_requests * BASE_COST_PER_REQUEST
    optimized_cost = total_requests * OPTIMIZED_COST_PER_REQUEST

    return {
        "requests": total_requests,
        "base_cloud_cost": round(base_cost, 2),
        "optimized_cloud_cost": round(optimized_cost, 2),
        "savings": round(base_cost - optimized_cost, 2)
    }
