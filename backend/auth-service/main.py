from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import jwt
import datetime

SECRET = "supersecretkey"
ALGORITHM = "HS256"

app = FastAPI(title="Auth Service")

# ==============================
# CORS CONFIG
# ==============================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==============================
# MOCK USER STORE (Prototype)
# ==============================
# In production this will be DB
USERS = {
    "9999999999": "citizen",
    "8888888888": "govt_employee",
    "7777777777": "govt_admin",
    "6666666666": "admin",
}

# ==============================
# REQUEST MODELS
# ==============================
class LoginRequest(BaseModel):
    mobile_number: str


# ==============================
# HEALTH CHECK
# ==============================
@app.get("/health")
def health():
    return {"status": "ok", "service": "auth"}


# ==============================
# LOGIN
# ==============================
@app.post("/auth/login")
def login(req: LoginRequest):

    role = USERS.get(req.mobile_number)

    if not role:
        raise HTTPException(status_code=401, detail="User not registered")

    payload = {
        "mobile": req.mobile_number,
        "role": role,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=6)
    }

    token = jwt.encode(payload, SECRET, algorithm=ALGORITHM)

    return {
        "message": "Login successful",
        "token": token,
        "role": role
    }


# ==============================
# VERIFY TOKEN
# ==============================
@app.post("/auth/verify")
def verify(token: str):
    try:
        decoded = jwt.decode(token, SECRET, algorithms=[ALGORITHM])
        return {
            "valid": True,
            "mobile": decoded["mobile"],
            "role": decoded["role"]
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
