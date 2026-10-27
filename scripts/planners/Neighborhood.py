#    This code is distributed WITHOUT ANY WARRANTY, without the implied
#   warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#   See the GNU Lesser General Public License for more details.

#   The license is distributed along with this repository or you can check
#   <http://www.gnu.org/licenses/> for more details.

# Contributors:
# marcos-pereira (https://github.com/marcos-pereira)

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