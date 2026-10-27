#    This code is distributed WITHOUT ANY WARRANTY, without the implied
#   warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#   See the GNU Lesser General Public License for more details.

#   The license is distributed along with this repository or you can check
#   <http://www.gnu.org/licenses/> for more details.

# Contributors:
# marcos-pereira (https://github.com/marcos-pereira)

from abc import ABC, abstractmethod

class State(ABC):
    """ Abstract state of a state space, e.g., a point in R^n. Concrete subclasses
    define how the state is represented.
    """

    @abstractmethod
    def get_value(self):
        """ Return the value that represents this state. """
        pass

    @abstractmethod
    def set_value(self, value):
        """ Set the value that represents this state. """
        pass
