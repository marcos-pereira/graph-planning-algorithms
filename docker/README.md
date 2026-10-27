# Docker — graph-planning-algorithms

Runs the scripts in `scripts/` (breadth-first planner on a grid map) in a container.

| Item | Value |
|------|-------|
| Image | `graph-planning-algorithms:latest` |
| Base | `python:3.12-slim` |
| Dependencies | `scripts/requirements.txt` (`numpy`, `opencv-python-headless`) |
| Volume | `scripts/` → `/workspace` (code changes need no rebuild) |

No display is needed: `main.py` loads the map with `test=True`, so no OpenCV window is opened.

## Quick Start

All commands from the project root.

```bash
# 1 — Optional: copy the parameter template and edit it
cp docker/.env.example docker/.env

# 2 — Build the image
docker compose -f docker/docker-compose.yml build

# 3 — Run main.py on the map set in docker/.env
docker compose -f docker/docker-compose.yml run --rm graph-planner
```

## Examples

```bash
# Another map, with its own start and goal
docker compose -f docker/docker-compose.yml run --rm graph-planner python3 main.py maps/smile.png 0 0 799 599

# Shell inside the container
docker compose -f docker/docker-compose.yml run --rm graph-planner bash
```

## CLI Arguments (`main.py`)

```
python3 main.py <map_file> <start_x> <start_y> <goal_x> <goal_y>
```

`map_file` is a path relative to `scripts/`, e.g. `maps/simplemaze.png`. The start and goal must be free cells. `x` is the column and `y` is the row of the map image. Defaults come from `docker/.env` (`START_X`, `START_Y`, `GOAL_X`, `GOAL_Y`): on `simplemaze.png`, `(x=418, y=0)` to `(x=610, y=861)`, the maze opening and exit. The printed path lists nodes as `(row, column)`, i.e. `(y, x)`.

## Notes

- `load_map` writes `no_background.png` to the working directory, i.e. `scripts/` on the host.
- The container runs as `HOST_UID:HOST_GID` (default `1000:1000`) so files it writes belong to you. Set them in `docker/.env` if your ids differ.
- Rebuild only when `scripts/requirements.txt` changes: `docker compose -f docker/docker-compose.yml build`.
