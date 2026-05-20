from class_network import Network, Hub, Drone, DroneStatus, Zone
from class_parser import MapParser
from typing import List, Dict, Set
from enum import Enum
from collections import deque


class Simulatior:
    """
    """
    def __init__(self, map: str) -> None:
        self.map = MapParser(map)
        print(self.map.data)
        self.net = Network(**self.map.data)
        self.drones_left: List[Drone] = self.net.start_hub.drone_bay
        self.drones_in_motion: List[Drone] = []
        self.graph: Dict[str, Hub] = {hub.name: hub.links for hub in self.net.hub}
        self.all_paths: List[List[Hub]] = self._find_all_paths()
    
    def _find_all_paths(self,
                        start: Hub = None,
                        visited: Set[Hub] = None,
                        current_path: List[Hub] = None,
                        all_paths: List[List[Hub]] = None) -> List[List[Hub]]:
        """
        """
        if start is None:
            start = self.net.start_hub
        if visited is None:
            visited = set()
        if current_path is None:
            current_path = []
        if all_paths is None:
            all_paths = []
        
        visited.add(start.name)
        current_path.append(start)

        if start == self.net.end_hub:
            all_paths.append(list(current_path))
        else:
            for link in start.links:
                if link['target_hub'].zone == Zone.BLOCKED:
                    continue
                if link['target_hub'].name not in visited:
                    self._find_all_paths(
                        link['target_hub'], visited, current_path, all_paths
                        )
        
        current_path.pop()
        visited.remove(start.name)

        return all_paths


    
    def simulate_turn(self) -> None:
        """
        """
        ...
    
    def output_turn(self) -> str:
        """
        """
        active_drones = [
            drone for drone in self.drones_left
            if drone.status == DroneStatus.DISPATCHED
            or drone.status == DroneStatus.TRANSIT 
            ]
        drone_strings = []
        for drone in active_drones:
            string = (
                f"{drone.id}-"
                f"{drone.current_hub if drone.status == DroneStatus.DISPATCHED
                   else drone.flying_to}"
                )
            drone_strings.append(string)
        
        return " ".join(drone_strings)
    
