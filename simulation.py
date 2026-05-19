from class_network_parser import Network, Hub, Drone, DroneStatus, Zone
from enum import Enum
from collections import deque


class Simulation:
    """
    """
    def __init__(self, map: str) -> None:
        self.net = Network.parser(map)
        self.net.connect_links()
        self.net.start_drones()
    
    def find_linear_path(self) -> deque:
        """
        """
        current_hub = self.net.start_hub
        turns = 0
        while current_hub != self.net.end_hub:

        for hub in self.net.hub:
            visited = []
            for link in hub.links:
                for edge, max in link.items():

    
    def simulate_turn(self) -> None:
        """
        """
        ...
