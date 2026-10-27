from .Neighborhood import Neighborhood

class EightNeighborhood(Neighborhood):
    def __init__(self):
        super().__init__()

    def get_neighbors(self, node: tuple[int, int]) -> list[tuple[int, int]]:
        """ Get the eight neighbors of a given node in the graph.

        Args:
            node (tuple[int, int]): The current node represented as a tuple (x, y).

        Returns:
            list[tuple[int, int]]: A list of neighboring nodes in the four cardinal directions.
        """
        x, y = node
        return [(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1), (x - 1, y - 1), (x - 1, y + 1), (x + 1, y - 1), (x + 1, y + 1)]