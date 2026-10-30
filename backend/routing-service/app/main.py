# backend/routing-service/app/main.py
import os
import uuid
import math
from typing import List, Dict

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from shared.database import get_db
from shared.models import User, Request as ServiceRequest, RoutePlan, RoutePlanNode
from shared.utils import log_event

app = FastAPI(title="Routing Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class RouteGenerateRequest(BaseModel):
    govt_user_id: uuid.UUID
    category: str
    region_id: uuid.UUID
    start_lat: float
    start_lng: float

def haversine(lat1, lng1, lat2, lng2) -> float:
    R = 6371  # Earth radius in km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
    return 2 * R * math.asin(math.sqrt(a))

def build_distance_matrix(nodes: List[Dict]) -> List[List[float]]:
    n = len(nodes)
    matrix = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i != j:
                matrix[i][j] = haversine(
                    nodes[i]["latitude"], nodes[i]["longitude"],
                    nodes[j]["latitude"], nodes[j]["longitude"]
                )
    return matrix

def route_distance(route: List[int], dist_matrix: List[List[float]]) -> float:
    return sum(dist_matrix[route[i]][route[i+1]] for i in range(len(route) - 1))

def nearest_neighbour(start_lat: float, start_lng: float, nodes: List[Dict], dist_matrix: List[List[float]]) -> List[int]:
    n = len(nodes)
    unvisited = set(range(n))
    route = []

    start_distances = [
        haversine(start_lat, start_lng, nodes[i]["latitude"], nodes[i]["longitude"])
        for i in range(n)
    ]
    current = min(range(n), key=lambda i: start_distances[i])
    route.append(current)
    unvisited.remove(current)

    while unvisited:
        nearest = min(unvisited, key=lambda j: dist_matrix[current][j])
        route.append(nearest)
        unvisited.remove(nearest)
        current = nearest

    return route

def two_opt(route: List[int], dist_matrix: List[List[float]]) -> List[int]:
    improved = True
    best_route = route[:]

    while improved:
        improved = False
        for i in range(1, len(best_route) - 1):
            for j in range(i + 1, len(best_route)):
                new_route = best_route[:i] + best_route[i:j+1][::-1] + best_route[j+1:]
                if route_distance(new_route, dist_matrix) < route_distance(best_route, dist_matrix):
                    best_route = new_route
                    improved = True
                    break
            if improved:
                break
    return best_route

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/generate")
async def generate_route(payload: RouteGenerateRequest, db: AsyncSession = Depends(get_db)):
    # Fetch active requests for this region and category
    result = await db.execute(
        select(ServiceRequest)
        .where(ServiceRequest.region_id == payload.region_id, 
               ServiceRequest.category == payload.category, 
               ServiceRequest.status == "active")
    )
    requests = result.scalars().all()
    
    if not requests:
        raise HTTPException(status_code=404, detail="No active requests found for this category in region.")

    nodes = [
        {"request_id": r.request_id, "latitude": float(r.latitude), "longitude": float(r.longitude)}
        for r in requests
    ]
    
    dist_matrix = build_distance_matrix(nodes)
    raw_route = nearest_neighbour(payload.start_lat, payload.start_lng, nodes, dist_matrix)
    optimised_route = two_opt(raw_route, dist_matrix)

    # Persist route plan
    route_plan = RoutePlan(
        created_by=payload.govt_user_id,
        category=payload.category,
        start_lat=payload.start_lat,
        start_lng=payload.start_lng
    )
    db.add(route_plan)
    await db.flush()

    for order, node_idx in enumerate(optimised_route):
        node = RoutePlanNode(
            route_id=route_plan.route_id,
            request_id=nodes[node_idx]["request_id"],
            visit_order=order
        )
        db.add(node)

    await db.commit()

    await log_event(
        actor_id=payload.govt_user_id,
        action_type="ROUTE_GENERATED",
        entity_type="route_plan",
        entity_id=route_plan.route_id
    )

    return {
        "route_id": str(route_plan.route_id),
        "ordered_nodes": [
            {
                "request_id": str(nodes[optimised_route[i]]["request_id"]),
                "latitude": nodes[optimised_route[i]]["latitude"],
                "longitude": nodes[optimised_route[i]]["longitude"],
                "visit_order": i
            }
            for i in range(len(optimised_route))
        ]
    }
