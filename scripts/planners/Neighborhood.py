from abc import ABC, abstractmethod

class Neighborhood(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def get_neighbors(self, node: tuple[int, int]) -> list[tuple[int, int]]:
        """ Get the neighbors of a given node in the graph.

        Raises:
            NotImplementedError: If the method is not implemented by subclasses.

        Returns:
            list[tuple[int, int]]: A list of neighboring nodes.
        """
        raise NotImplementedError("The get_neighbors method must be implemented by subclasses.")