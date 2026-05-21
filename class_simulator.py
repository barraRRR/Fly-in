from class_network import Network, Hub, Drone, DroneStatus, Zone
from class_parser import MapParser
from typing import List, Dict, Set, Tuple
from enum import Enum
from collections import deque


class HubFullError(Exception):
    pass


class NoLinksAvailableError(Exception):
    pass


class DroneCantMove(Exception):
    pass


class Simulator:
    """
    """
    def __init__(self, map: str) -> None:
        self.turn_num: int = 0
        self.map = MapParser(map)
        print(self.map.data)
        self.net = Network(**self.map.data)
        self.drones_left: List[Drone] = self.net.start_hub.drone_bay
        self.drones_in_motion: List[Drone] = []
        self.graph: Dict[str, Hub] = {hub.name: hub.links for hub in self.net.hub}
        self.all_paths: List[Dict[str, List[Hub], int, int]] = self._find_all_paths()

        for drone in self.net.start_hub:
            drone.visited.append(self.net.start_hub)
    
    def _find_all_paths(
            self,
            start: Hub = None,
            visited: Set[Hub] = None,
            current_path: List[Hub] = None,
            all_paths: List[List[Hub]] = None
            ) -> List[Dict[str, List[Hub]], int, int]:
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

        dict_paths = []
        count = 0
        for path in all_paths:
            total_hubs, total_turns, _, _, _ = self._route_status(path, path[0])
            id = f"route_{count:03d}"
            dict_paths.append(
                {
                    "id": id,
                    "path": path,
                    "total_hubs": total_hubs,
                    "total_turns": total_turns,
                }
            )

        return dict_paths

    def _route_status(self, current_hub: Hub, route: List[Hub]) -> Tuple[bool, int]:
        """
        """
        hub_index = route.index(current_hub)
        hubs_left = route[hub_index:]
        next_hub = route[hub_index + 1]
        remaining_turns = (
            len([hub for hub in hubs_left]) +
            len([hub for hub in hubs_left if hub.zone == Zone.RESTRICTED])
        )
        priority_next = True if next_hub.zone == Zone.PRIORITY else False
        available_space = True if len(next_hub.drone_bay) < next_hub.max_drones else False

        return (
            hubs_left, remaining_turns, next_hub,
            priority_next, available_space
            )
    
    def _available_connection(self, origin: Hub, dest: Hub) -> bool:
        """
        """
        for link in origin.links:
            if (link['target_hub'] == dest and
                (link['max'] > link['incoming_drones'])):
                    return True
            else:
                return False
        return False
    
    def _flight_planner(self, drone: Drone) -> None:
        """
        """
        available_paths = [
            path for path in self.all_paths if
            drone.current_hub in path["path"]
            ]
        if available_paths == None:
            raise DroneCantMove

        evaluated_paths = []
        for path_template in available_paths:
            path = path_template.copy()
            (
                hubs_left,
                remaining_turns,
                next_hub,
                priority_next,
                available_space,
            ) = self._route_status(drone.current_hub, path["path"])
        
            path["path"] = hubs_left
            path["total_turns"] = remaining_turns
            path["next_hub"] = next_hub
            path["priority_next"] = priority_next
            path["available_space"] = available_space
            path["total_hubs"] = len(hubs_left)
            path["available_connection"] = self._available_connection(
                drone.current_hub, next_hub
            )
            evaluated_paths.append(path)

        valid_paths = [
            p for p in evaluated_paths
            if p["available_space"] and p["available_connection"]
        ]

        if not valid_paths:
            raise DroneCantMove

        priority_choices = [
            p for p in valid_paths if p["priority_next"]
        ]
        final_choices = priority_choices if priority_choices else valid_paths
        chosen_path = min(final_choices, key=lambda p: p["total_turns"])
        drone.destination = chosen_path["next_hub"]
        drone.remaining_turns = chosen_path["total_turns"]

    def _take_off(self, drone: Drone) -> None:
        """
        """

        drone.current_hub.drone_bay.remove(drone)
        for link in drone.current_hub.links:
            if link['target_hub'] == drone.destination:
                link['incoming_drones'] += 1
        for link in drone.destination.links:
            if link['target_hub'] == drone.current_hub:
                link['incoming_drones'] += 1
        drone.current_hub = None
        if drone.destination.zone == Zone.RESTRICTED:
            drone.status = DroneStatus.RESTRICTED_FLIGHT
        else:
            drone.status = DroneStatus.FLYING
        self.drones_in_motion.append(drone)

    def _arrive(self, drone: Drone) -> None:
        """
        """
        if drone.destination.hub_type != "end_hub":
            drone.destination.drone_bay.append(drone)
        drone.current_hub = drone.destination
        drone.destination = None
        drone.status = (
            DroneStatus.DELIVERED if drone.current_hub.type == "end_hub"
            else DroneStatus.ARRIVED
        )
        if drone.status == DroneStatus.DELIVERED:
            self.drones_left.remove(drone)
        elif drone.status == DroneStatus.ARRIVED:
            self.drones_in_motion.remove(drone)

        for link in drone.current_hub.links:
            if link['target_hub'] == drone.visited_hubs[-1]:
                link['incoming_drones'] -= 1
        
        for link in drone.visited_hubs[-1].links:
            if link['target_hub'] == drone.current_hub:
                link['incoming_drones'] -= 1
        
        drone.visited_hubs.append(drone.current_hub)


    def _simulate_turn(self) -> None:
        """
        """
        self.turn_num += 1

        available_drones = []
        for drone in self.drones_left:
            if drone.status == DroneStatus.RESTRICTED_FLIGHT:
                drone.status = DroneStatus.FLYING
            elif drone.status == DroneStatus.ARRIVED:
                drone.status = DroneStatus.STANDBY
                available_drones.append(drone)
        
        available_drones.sort(key=lambda p: p.remaining_turns, reverse=True)
        
        while available_drones:
            try:
                fewer_turns = available_drones.pop()
                self._flight_planner(fewer_turns)
                self._take_off(fewer_turns)
            
            except DroneCantMove:
                available_drones.remove(drone)
                continue

        self._output_turn()

        for drone in self.drones_in_motion:
            if drone.status == DroneStatus.FLYING:
                self._arrive(drone)
    
    def start_simulation(self) -> None:
        """
        """
        while self.drones_left:
            print(f"TURN: {self.turn_num:03d}")
            self._simulate_turn
            print()
    
    def _output_turn(self) -> str:
        """
        """
        active_drones = [
            drone for drone in self.drones_left
            if drone.status == DroneStatus.FLYING
            or drone.status == DroneStatus.RESTRICTED_FLIGHT 
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
    

