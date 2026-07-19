from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from routing import load_graph, get_routes, get_boundary

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
    chaos: int = 0
    avoid_highways: int = 0
    love_bridges: int = 0


@app.get("/api/boundary")
def get_boundary_endpoint():
    try:
        return get_boundary()
    except Exception as e:
        return {"error": str(e)}


@app.post("/api/route")
def calculate_route(req: RouteRequest):
    routes = get_routes(req)
    return {
        "status": "success" if routes["normal"] else "failed",
        "normal_route": routes["normal"],
        "nah_route": routes["nah"],
        "normal_stats": routes.get("normal_stats"),
        "nah_stats": routes.get("nah_stats"),
        "message": "Calculated."
    }


@app.get("/api/health")
def health_check():
    return {"status": "healthy", "message": "Backend is running terribly efficiently."}
