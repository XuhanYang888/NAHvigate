from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from routing import load_graph, get_shortest_path

app = FastAPI(title="NAHvigate API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event():
    load_graph()


class RouteRequest(BaseModel):
    start_lat: float
    start_lon: float
    end_lat: float
    end_lon: float


@app.post("/api/route")
def calculate_route(req: RouteRequest):
    coords = get_shortest_path(
        req.start_lat, req.start_lon, req.end_lat, req.end_lon)
    return {
        "status": "success" if coords else "failed",
        "route": coords,
        "message": "Calculated the most boring route possible."
    }


@app.get("/api/health")
def health_check():
    return {"status": "healthy", "message": "Backend is running terribly efficiently."}
