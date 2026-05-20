from class_network import Network, Drone, Hub
from class_parser import MapParser
from class_simulator import Simulatior

"""
map = MapParser("./maps/easy/01_linear_path.txt")
print(map.data)
net = Network(**map.data)
print(net.get_map_info())
"""

sim = Simulatior("./maps/easy/01_linear_path.txt")
print(sim.net.get_map_info())

print(len(sim.paths))
