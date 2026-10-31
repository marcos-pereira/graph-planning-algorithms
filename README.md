# graph-planning-algorithms

Implementations of graph search planners (breadth-first, depth-first and A* search) on grid maps in Python, with a command-line interface and a browser-based (PixiJS) visualization. Planners can use a four- or an eight-neighbour grid.

## Quick test with browser visualizer using docker

```bash
# 1 — Build the web visualizer image
docker compose -f docker/docker-compose.yml --profile webvis build

# 2a — Run the web visualizer, then open http://localhost:8000
docker compose -f docker/docker-compose.yml --profile webvis up

# 2b — Run the command-line planner instead (prints the path in the terminal)
docker compose -f docker/docker-compose.yml build graph-planner
docker compose -f docker/docker-compose.yml run --rm graph-planner
```

Next, open **http://localhost:8000** in your browser. Select an algorithm, a neighborhood and a map, set the start and goal (type them or use the click buttons), adjust the animation speed, and click **Run**. Step 2b instead prints the planned path in the terminal — see [Running the command-line planner](#running-the-command-line-planner) below.

---

## Quick view of the software architecture

See [`docs/uml-class-diagram.md`](docs/uml-class-diagram.md) for the UML class diagram (Mermaid source) and design notes.

A `GraphPlanner` is built from the occupancy grid, a `Neighborhood` (which nodes can be reached from a node) and a `CollisionChecker` (which nodes are free). `plan(start, goal)` returns the list of nodes of the path from the start to the goal, both included, or an empty list if there is no path. Nodes are `(row, column)` tuples of the map matrix. After planning, `planner.parent` holds the discovered nodes in discovery order, which the web visualizer animates.

| Planner | Strategy | Path |
|---|---|---|
| `BreadthFirstPlanner` | Queue (FIFO) | Fewest steps |
| `DepthFirstPlanner` | Stack (LIFO) | A valid path, usually much longer |
| `AStarPlanner` | Priority queue on `f = g + h` (Euclidean distance as edge cost and heuristic) | Shortest path (lowest total cost) |

| Neighborhood | Moves |
|---|---|
| `FourNeighborhood` | Up, down, left, right |
| `EightNeighborhood` | The four above plus the four diagonals |

---

## Setup

Create and activate a virtual environment, then install all dependencies:

```bash
virtualenv my_venv
source my_venv/bin/activate
pip install -r scripts/requirements.txt -r webvis/requirements.txt
```

---

## Running the command-line planner

```bash
cd scripts
python3 main.py <map> <x0> <y0> <xg> <yg>
```

| Argument | Description |
|---|---|
| `map` | PNG map file, relative to `scripts/` (e.g. `maps/simplemaze.png`) |
| `x0 y0` | Start coordinates: `x` is the column and `y` the row of the map image |
| `xg yg` | Goal coordinates, in the same convention |

The start and goal must be free cells of the map. Example commands:

```bash
python3 main.py maps/simplemaze.png 418 0 610 861
python3 main.py maps/smile.png 0 0 799 599
```

`main.py` runs `BreadthFirstPlanner` with `FourNeighborhood` and prints the path as a list of `(row, column)` nodes. If the start or goal is out of bounds or on an obstacle, it prints a warning and the path is empty. The map is loaded without opening a window, and `no_background.png` is written to the current directory.

---

## Running the web visualizer

The web visualizer runs in a browser using PixiJS.

```bash
cd webvis
uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

Open **http://localhost:8000**. Select an **algorithm** (BFS, DFS or A*), a **neighborhood** (four or eight neighbors) and a map, set the start and goal, adjust the animation speed, and click **Run**. The search runs on the server first, then the page animates the explored cells in discovery order and draws the path in blue. The **Speed** slider sets how many cells are drawn per frame.

The page uses a single endpoint, `GET /plan`:

| Parameter | Description |
|---|---|
| `map_name` | PNG map file in `scripts/maps/`. Defaults to `simplemaze.png`. |
| `x0 y0` | Start coordinates (`x` is the column, `y` the row). Default `418 0`. |
| `xg yg` | Goal coordinates. Default `610 861`. |
| `planner` | `bfs` (default), `dfs` or `astar`. |
| `neighborhood` | `four` (default) or `eight`. |

An unknown planner or neighborhood, or a start or goal on an obstacle, returns HTTP 400 with the reason. Only one planning run is allowed at a time; a second request gets HTTP 429 until the first finishes.

> If the page looks broken or out of date after an update (e.g. the map never loads), do a hard refresh (Ctrl+Shift+R / Cmd+Shift+R) to bypass a stale browser cache of its JS.

---

## Running with Docker

See [`docker/README.md`](docker/README.md) for full instructions. Quick start:

```bash
# Optional: copy the parameter template (map, start and goal for the command-line planner)
cp docker/.env.example docker/.env

# Command-line planner
docker compose -f docker/docker-compose.yml build graph-planner
docker compose -f docker/docker-compose.yml run --rm graph-planner

# Command-line planner with other arguments
docker compose -f docker/docker-compose.yml run --rm graph-planner python3 main.py maps/smile.png 0 0 799 599

# Web visualizer — open http://localhost:8000
docker compose -f docker/docker-compose.yml --profile webvis build
docker compose -f docker/docker-compose.yml --profile webvis up
```

---

## Adding new maps

The map must be a black-and-white PNG with obstacles in black. Put it in `scripts/maps/`; the web visualizer lists every PNG in that folder.
