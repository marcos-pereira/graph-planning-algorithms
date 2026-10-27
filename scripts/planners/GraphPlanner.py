import numpy as np
from abc import ABC, abstractmethod
from .Neighborhood import Neighborhood
from utils.CollisionChecker import CollisionChecker

class GraphPlanner(ABC):
    def __init__(self, graph : np.ndarray, neighborhood: Neighborhood, collision_checker: CollisionChecker):
        """ Initialize the GraphPlanner with a graph, a neighborhood and a collision checker.

        Args:
            graph (np.ndarray): The graph represented as a 2D array.
            neighborhood (Neighborhood): The neighborhood structure to use for finding neighbors.
            collision_checker (CollisionChecker): The collision checker used to validate nodes.
        """
        self.graph = graph
        self.neighborhood = neighborhood
        self.collision_checker = collision_checker

    @abstractmethod
    def plan(self, start : tuple[int, int], goal : tuple[int, int]) -> list[tuple[int, int]]:
        """ Compute the plan.

        Args:
            start (tuple[int, int]): Start node.
            goal (tuple[int, int]): Goal node.

        Raises:
            NotImplementedError: If the method is not implemented by subclasses.

        Returns:
            list[tuple[int, int]]: The planned path from start to goal.
        """
        raise NotImplementedError("The plan method must be implemented by subclasses.")

    @abstractmethod
    def is_valid(self, node : tuple[int, int]) -> bool:
        """ Check if a node is valid (within bounds and not an obstacle).

        Args:
            node (tuple[int, int]): The node to check.

        Raises:
            NotImplementedError: If the method is not implemented by subclasses.

        Returns:
            bool: True if the node is valid, False otherwise.
        """
        raise NotImplementedError("The is_valid method must be implemented by subclasses.")