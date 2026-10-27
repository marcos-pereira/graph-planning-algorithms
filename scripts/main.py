#!/usr/bin/env python3

import sys 

from utils.Map import load_map
from utils.Cartesian2DCollisionChecker import Cartesian2DCollisionChecker
from planners.BreadthFirstPlanner import BreadthFirstPlanner
from planners.FourNeighborhood import FourNeighborhood

def main():
    if len(sys.argv) != 6:
        print("Usage: python main.py <map_file> <start_x> <start_y> <goal_x> <goal_y>")
        sys.exit(1)

    map_file = sys.argv[1]
    start_x = int(sys.argv[2])
    start_y = int(sys.argv[3])
    goal_x = int(sys.argv[4])
    goal_y = int(sys.argv[5])

    # Skip the blocking OpenCV window
    graph = load_map(map_file, test=True)
    neighborhood = FourNeighborhood()
    # The collision checker built from the obstacles of the map
    collision_checker = Cartesian2DCollisionChecker(graph)
    planner = BreadthFirstPlanner(graph, neighborhood, collision_checker)
    # The planner nodes are (row, col) = (y, x) of the map
    path = planner.plan((start_y, start_x), (goal_y, goal_x))
    print(f"Planned path: {path}")

if __name__ == "__main__":
    main()