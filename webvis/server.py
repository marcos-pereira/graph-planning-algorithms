import os
import sys
import threading
import time
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

# Allow overriding the scripts directory via env var for Docker
SCRIPTS_DIR = Path(os.environ.get("SCRIPTS_DIR", Path(__file__).parent.parent / "scripts")).resolve()
MAPS_DIR = SCRIPTS_DIR / "maps"
# Limits planning to one run at a time across all clients, so a handful of browser
# tabs can't each kick off a full search and exhaust the server's CPU.
PLANNING_SEMAPHORE = threading.Semaphore(1)
sys.path.insert(0, str(SCRIPTS_DIR))

from utils.Map import load_map
from utils.Cartesian2DCollisionChecker import Cartesian2DCollisionChecker
from planners.BreadthFirstPlanner import BreadthFirstPlanner
from planners.DepthFirstPlanner import DepthFirstPlanner
from planners.FourNeighborhood import FourNeighborhood
from planners.EightNeighborhood import EightNeighborhood

# The planners selectable through the planner query parameter of /plan
PLANNERS = {
    "bfs": BreadthFirstPlanner,
    "dfs": DepthFirstPlanner,
}

# The neighborhoods selectable through the neighborhood query parameter of /plan
NEIGHBORHOODS = {
    "four": FourNeighborhood,
    "eight": EightNeighborhood,
}

app = FastAPI(title="Graph Planner Web Visualizer")


@app.middleware("http")
async def no_cache_static_assets(request, call_next):
    """Force browsers to revalidate static/ files (HTML/JS/CSS) on every request
    instead of serving a stale cached copy after a deploy. Revalidation still lets
    the browser skip the download via a 304 when the file is unchanged."""
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-cache"
    return response


def _resolve_map_path(map_name: str) -> Path:
    """Validate map_name and return its path, without exposing the rest of MAPS_DIR."""
    map_path = (MAPS_DIR / map_name).resolve()
    if map_path.parent != MAPS_DIR or map_path.suffix.lower() != ".png" or not map_path.is_file():
        raise HTTPException(status_code=404, detail=f"Map '{map_name}' not found.")
    return map_path


def _acquire_planning_slot():
    """Reserve the single planning slot, or raise 429 immediately if one is already
    in use."""
    if not PLANNING_SEMAPHORE.acquire(blocking=False):
        raise HTTPException(
            status_code=429,
            detail="A planning job is already running. Please wait for it to finish before starting another.",
        )


@app.get("/maps-list")
def list_maps():
    """Return names of available PNG map files."""
    skip = {"no_background.png"}
    return sorted(f.name for f in MAPS_DIR.glob("*.png") if f.name not in skip)


@app.get("/maps/{map_name}")
def get_map(map_name: str):
    """Serve a single PNG map file without exposing the entire scripts/ directory."""
    map_path = _resolve_map_path(map_name)
    return FileResponse(map_path, media_type="image/png")


@app.get("/plan")
def compute_plan(
    map_name: str = "simplemaze.png",
    x0: int = Query(418, ge=0),
    y0: int = Query(0, ge=0),
    xg: int = Query(610, ge=0),
    yg: int = Query(861, ge=0),
    planner_name: str = Query("bfs", alias="planner"),
    neighborhood_name: str = Query("four", alias="neighborhood"),
):
    """Run the selected planner (bfs or dfs) with the selected neighborhood (four or
    eight) and return the explored cells in discovery order plus the path. Coordinates
    are (x, y) = (column, row) of the map image, while the planner nodes are
    (row, column), so they are swapped on the way in and out.

    explored is a flat [x0, y0, x1, y1, ...] list to keep the response small, since
    the search can discover hundreds of thousands of cells on a large map.
    """
    if planner_name not in PLANNERS:
        raise HTTPException(status_code=400, detail=f"Unknown planner '{planner_name}'. Available: {', '.join(PLANNERS)}.")
    if neighborhood_name not in NEIGHBORHOODS:
        raise HTTPException(status_code=400, detail=f"Unknown neighborhood '{neighborhood_name}'. Available: {', '.join(NEIGHBORHOODS)}.")
    _resolve_map_path(map_name)
    _acquire_planning_slot()
    try:
        try:
            scene_map = load_map(map_name, test=True, maps_dir=MAPS_DIR)
        except Exception:
            raise HTTPException(status_code=400, detail=f"Failed to load map '{map_name}'.")
        map_height, map_width = scene_map.shape

        neighborhood = NEIGHBORHOODS[neighborhood_name]()
        collision_checker = Cartesian2DCollisionChecker(scene_map)
        planner = PLANNERS[planner_name](scene_map, neighborhood, collision_checker)

        start = (y0, x0)
        goal = (yg, xg)
        if not planner.is_valid(start):
            raise HTTPException(status_code=400, detail=f"Start ({x0}, {y0}) is out of bounds or on an obstacle.")
        if not planner.is_valid(goal):
            raise HTTPException(status_code=400, detail=f"Goal ({xg}, {yg}) is out of bounds or on an obstacle.")

        planning_start_time = time.perf_counter()
        path = planner.plan(start, goal)
        planning_time = time.perf_counter() - planning_start_time

        explored = [coordinate for row, col in planner.parent for coordinate in (int(col), int(row))]

        return {
            "explored": explored,
            "path": [[int(col), int(row)] for row, col in path],
            "map_width": int(map_width),
            "map_height": int(map_height),
            "x_init": [x0, y0],
            "x_goal": [xg, yg],
            "explored_count": len(planner.parent),
            "path_found": len(path) > 0,
            "planning_time": planning_time,
            "map_name": map_name,
            "planner": planner_name,
            "neighborhood": neighborhood_name,
        }
    finally:
        PLANNING_SEMAPHORE.release()


# Serve the PixiJS frontend
app.mount("/", StaticFiles(directory=str(Path(__file__).parent / "static"), html=True), name="static")
