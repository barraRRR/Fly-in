from class_network import Network, Hub, Drone, DroneStatus, Zone
from class_parser import MapParser
from enum import Enum
from collections import deque


class Simulatior:
    """
    """
    def __init__(self, map: str) -> None:
        self.map = MapParser(map)
        self.net = Network(**self.map.data)
    
    def find_linear_path(self) -> deque:
        """
        """
        total_paths = []
        while True:
            current_hub = self.net.start_hub
            path = deque()
            while current_hub != self.net.end_hub:
                path.append(current_hub)

            for hub in self.net.hub:
                visited = []
                for link in hub.links:
                    for edge, max in link.items():

    
    def simulate_turn(self) -> None:
        """
        """
        ...
