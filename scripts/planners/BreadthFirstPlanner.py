from collections import deque

from .GraphPlanner import GraphPlanner
from utils.RealVectorState import RealVectorState

class BreadthFirstPlanner(GraphPlanner):
    def plan(self, start : tuple[int, int], goal : tuple[int, int]) -> list[tuple[int, int]]:
        """ Compute the plan using Breadth-First Search (BFS).

        Args:
            start (tuple[int, int]): Start node.
            goal (tuple[int, int]): Goal node.

        Returns:
            list[tuple[int, int]]: The planned path from start to goal, or an
            empty list if start or goal is invalid or no path exists.
        """
        # Discovered nodes mapped to their predecessor, which also acts as the visited set.
        # Kept after planning so the search can be inspected; insertion order is the
        # BFS discovery order.
        self.parent = {}

        # Both endpoints must be inside the grid and free of obstacles
        if not self.is_valid(start) or not self.is_valid(goal):
            print(f"⚠️ Invalid start {start} or goal {goal}: out of bounds or on an obstacle")
            return []

        queue = deque([start])
        self.parent[start] = None

        while queue:
            current = queue.popleft()

            if current == goal:
                path = []
                while current is not None:
                    path.append(current)
                    current = self.parent[current]
                # return the path in reverse order (from start to goal)
                return path[::-1]

            # Explore the neighbors of the current node
            for neighbor in self.get_neighbors(current):
                # If the neighbor has not been discovered yet,
                # add it to the queue and set its parent
                if neighbor not in self.parent:
                    self.parent[neighbor] = current
                    queue.append(neighbor)

        return []  # Return an empty path if no path is found

    def get_neighbors(self, node : tuple[int, int]) -> list[tuple[int, int]]:
        """ Get the neighbors of a given node in the graph.

        Args:
            node (tuple[int, int]): The node for which to find neighbors.

        Returns:
            list[tuple[int, int]]: A list of neighboring nodes.
        """
        candidates = self.neighborhood.get_neighbors(node)
        return [candidate for candidate in candidates if self.is_valid(candidate)]

    def is_valid(self, node : tuple[int, int]) -> bool:
        """ Check if a node is valid (within bounds and not an obstacle).

        Args:
            node (tuple[int, int]): The node to check.

        Returns:
            bool: True if the node is valid, False otherwise.
        """
        row, col = node
        if not (0 <= row < self.graph.shape[0] and 0 <= col < self.graph.shape[1]):
            return False

        # The collision checker states are (x, y) = (col, row), while graph nodes are (row, col)
        state = RealVectorState((col, row))
        return not self.collision_checker.collision(state)