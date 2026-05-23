from class_network import Network, Drone, Hub
from class_parser import MapParser
from class_simulator import Simulator

"""
map = MapParser("./maps/easy/01_linear_path.txt")
print(map.data)
net = Network(**map.data)
print(net.get_map_info())
"""

sim = Simulator("./maps/easy/01_linear_path.txt")
sim.start_simulation()
