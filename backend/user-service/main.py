from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
import psycopg2
import os

app = FastAPI(title="User Service")

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

class User(BaseModel):
    name: str
    mobile_number: str
    role: str
    region: str

@app.on_event("startup")
def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        name TEXT,
        mobile TEXT UNIQUE,
        role TEXT,
        region TEXT
    )
    """)
    conn.commit()
    conn.close()

@app.get("/health")
def health():
    return {"status": "ok", "service": "user"}

@app.post("/users")
def create_user(user: User, authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing token")

    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO users (name, mobile, role, region) VALUES (%s, %s, %s, %s)",
            (user.name, user.mobile_number, user.role, user.region)
        )
        conn.commit()
    except Exception:
        raise HTTPException(status_code=400, detail="User already exists")
    finally:
        conn.close()

    return {"message": "User created"}

@app.get("/users/me")
def get_me(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing token")

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT name, mobile, role, region FROM users LIMIT 1")
    row = cur.fetchone()
    conn.close()

    if not row:
        return {"message": "No users found"}

    return {
        "name": row[0],
        "mobile": row[1],
        "role": row[2],
        "region": row[3]
    }
