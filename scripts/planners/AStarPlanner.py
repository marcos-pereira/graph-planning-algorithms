#    This code is distributed WITHOUT ANY WARRANTY, without the implied
#   warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#   See the GNU Lesser General Public License for more details.

#   The license is distributed along with this repository or you can check
#   <http://www.gnu.org/licenses/> for more details.

# Contributors:
# marcos-pereira (https://github.com/marcos-pereira)

import numpy as np
# Import heapq for priority queue implementation
import heapq

from .GraphPlanner import GraphPlanner
from utils.RealVectorState import RealVectorState
from utils.DistanceMetric import DistanceMetric
from .Neighborhood import Neighborhood
from utils.CollisionChecker import CollisionChecker

class AStarPlanner(GraphPlanner):
    def __init__(self, graph : np.ndarray, neighborhood: Neighborhood, collision_checker: CollisionChecker, distance_metric: DistanceMetric):
        super().__init__(graph, neighborhood, collision_checker)
        self.distance_metric = distance_metric

    def plan(self, start : tuple[int, int], goal : tuple[int, int]) -> list[tuple[int, int]]:
        """ Compute the plan using A* Search.

        Args:
            start (tuple[int, int]): Start node.
            goal (tuple[int, int]): Goal node.

        Returns:
            list[tuple[int, int]]: The planned path from start to goal, or an
            empty list if start or goal is invalid or no path exists.
        """
        # Discovered nodes mapped to their predecessor, which also acts as the visited set.
        # Kept after planning so the search can be inspected; insertion order is the
        # A* discovery order.
        self.parent = {}

        # Both endpoints must be inside the grid and free of obstacles
        if not self.is_valid(start) or not self.is_valid(goal):
            print(f"⚠️ Invalid start {start} or goal {goal}: out of bounds or on an obstacle")
            return []
        
        # Best known cost from the start to each discovered node
        self.g_cost = {start: 0.0}
        self.parent[start] = None

        # Priority queue ordered by f = g + h, with h breaking ties towards the goal.
        # Outdated entries are skipped lazily when popped instead of being removed.
        priority_queue = []
        start_heuristic = self.heuristic(start, goal)
        heapq.heappush(priority_queue, (start_heuristic, start_heuristic, start))

        # Nodes whose optimal cost is settled
        closed = set()

        while priority_queue:
            current = heapq.heappop(priority_queue)[2]

            if current in closed:
                continue
            closed.add(current)

            if current == goal:
                path = []
                while current is not None:
                    path.append(current)
                    current = self.parent[current]
                # return the path in reverse order (from start to goal)
                return path[::-1]

            # Explore the neighbors of the current node
            for neighbor in self.get_neighbors(current):
                if neighbor in closed:
                    continue

                # Keep the neighbor only if this route is cheaper than any found so far
                tentative_cost = self.g_cost[current] + self.edge_cost(current, neighbor)
                if tentative_cost < self.g_cost.get(neighbor, float("inf")):
                    self.g_cost[neighbor] = tentative_cost
                    self.parent[neighbor] = current
                    neighbor_heuristic = self.heuristic(neighbor, goal)
                    heapq.heappush(priority_queue, (tentative_cost + neighbor_heuristic, neighbor_heuristic, neighbor))

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
    
    def edge_cost(self, from_node : tuple[int, int], to_node : tuple[int, int]) -> float:
        """ Compute the cost of moving from one node to another.

        Args:
            from_node (tuple[int, int]): The starting node.
            to_node (tuple[int, int]): The destination node.
        
        Returns:
            float: The cost of moving from from_node to to_node.
        """
        return self.distance_metric.compute(from_node, to_node)
        
    def cost_to_start(self, node : tuple[int, int]) -> float:
        """ Compute the cost from the start node to the given node.

        Args:
            node (tuple[int, int]): The node for which to compute the cost.

        Returns:
            float: The cost from the start node to the given node.
        """
        return self.g_cost.get(node, float("inf"))
    
    def heuristic(self, node : tuple[int, int], goal : tuple[int, int]) -> float:
        """ Compute the heuristic cost from the given node to the goal node.

        Args:
            node (tuple[int, int]): The node for which to compute the heuristic.
            goal (tuple[int, int]): The goal node.

        Returns:
            float: The heuristic cost from the node to the goal.
        """
        return self.distance_metric.compute(node, goal)