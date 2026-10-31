from math import hypot
from .DistanceMetric import DistanceMetric

class EuclideanDistance(DistanceMetric):
    def compute(self, point1 : tuple[float, float], point2 : tuple[float, float]) -> float:
        """Compute the Euclidean distance between two points.

        Args:
            point1: The first point.
            point2: The second point.

        Returns:
            The computed Euclidean distance between the two points.
        """
        # Using the hypot function to compute the Euclidean distance because 
        # it is more numerically stable and avoids overflow/underflow issues.
        return hypot(point1[0] - point2[0], point1[1] - point2[1])