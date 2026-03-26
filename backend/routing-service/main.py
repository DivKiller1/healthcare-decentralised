from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import math
from auth_middleware import verify_token

app = FastAPI(title="Healthcare Routing Service v3.0")

# =========================
# CORS CONFIG
# =========================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# CONFIGURABLE WEIGHTS
# (You can tune these anytime)
# =========================
PRIORITY_WEIGHT = 5
DISTANCE_WEIGHT = 1
TRAFFIC_WEIGHT = 3


# =========================
# MODELS
# =========================
class RoutePoint(BaseModel):
    id: int
    lat: float
    lon: float
    category: Optional[str] = "clinic"


class RoutePayload(BaseModel):
    start_lat: float
    start_lon: float
    points: List[RoutePoint]


# =========================
# DISTANCE (HAVERSINE)
# =========================
def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # km

    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


# =========================
# PRIORITY SYSTEM
# Lower score = higher priority
# =========================
def priority_score(category: str):
    cat = (category or "").lower()

    if cat == "blood":
        return 0
    if cat == "emergency":
        return 0
    if cat == "polio":
        return 1
    return 2  # clinic default


# =========================
# TRAFFIC SIMULATION ZONES
# Replace later with live API
# =========================
def traffic_multiplier(lat, lon):
    """
    Simulated Dehradun Traffic Model
    """

    # Heavy traffic zone (ISBT / central)
    if 30.28 < lat < 30.30 and 78.00 < lon < 78.02:
        return 1.8

    # Medium traffic zone (Clock Tower)
    if 30.30 < lat < 30.31 and 78.02 < lon < 78.04:
        return 1.4

    # Low traffic outer zone
    return 1.0


# =========================
# COST FUNCTION
# =========================
def compute_weight(start_lat, start_lon, point: RoutePoint):
    distance = haversine(start_lat, start_lon, point.lat, point.lon)
    priority = priority_score(point.category)
    traffic = traffic_multiplier(point.lat, point.lon)

    weighted_cost = (
        PRIORITY_WEIGHT * priority +
        DISTANCE_WEIGHT * distance +
        TRAFFIC_WEIGHT * traffic
    )

    return weighted_cost, distance, traffic, priority


# =========================
# HEALTH CHECK
# =========================
@app.get("/health")
def health():
    return {
        "status": "routing-service-up",
        "version": "3.0",
        "features": [
            "priority-routing",
            "distance-weighting",
            "traffic-simulation",
            "jwt-protected"
        ]
    }


# =========================
# ROUTE OPTIMIZATION
# =========================
@app.post("/route/optimize")
def optimize_route(
    payload: RoutePayload,
    user=Depends(verify_token)
):
    if not payload.points:
        return {"visit_order": []}

    scored_points = []

    for point in payload.points:
        cost, distance, traffic, priority = compute_weight(
            payload.start_lat,
            payload.start_lon,
            point
        )

        scored_points.append({
            "id": point.id,
            "cost": cost,
            "distance_km": round(distance, 2),
            "traffic_multiplier": traffic,
            "priority_score": priority
        })

    # Sort by total weighted cost
    scored_points.sort(key=lambda x: x["cost"])

    visit_order = [p["id"] for p in scored_points]

    return {
        "visit_order": visit_order,
        "details": scored_points,
        "meta": {
            "weights": {
                "priority_weight": PRIORITY_WEIGHT,
                "distance_weight": DISTANCE_WEIGHT,
                "traffic_weight": TRAFFIC_WEIGHT
            }
        }
    }