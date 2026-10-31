#    This code is distributed WITHOUT ANY WARRANTY, without the implied
#   warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#   See the GNU Lesser General Public License for more details.

#   The license is distributed along with this repository or you can check
#   <http://www.gnu.org/licenses/> for more details.

# Contributors:
# marcos-pereira (https://github.com/marcos-pereira)

from abc import ABC, abstractmethod

class DistanceMetric(ABC):
    @abstractmethod
    def compute(self, point1 : tuple[float, float], point2 : tuple[float, float]) -> float:
        """Compute the distance between two points.

        Args:
            point1: The first point.
            point2: The second point.

        Returns:
            The computed distance between the two points.
        """
        pass