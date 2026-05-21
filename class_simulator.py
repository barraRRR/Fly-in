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
        self.drones_left: List[Drone] = [d for d in self.net.start_hub.drone_bay]
        self.drones_in_motion: List[Drone] = []
        self.graph: Dict[str, Hub] = {hub.name: hub.links for hub in self.net.hub}
        self.all_paths: List[Dict[str, List[Hub], int, int]] = self._find_all_paths()

        for drone in self.drones_left:
            drone.visited_hubs.append(self.net.start_hub)
    
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
            total_hubs, total_turns, _, _, _ = self._route_status(path[0], path)
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
        remaining_turns = int(
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
        return False
    
    def _flight_planner(self, drone: Drone) -> None:
        """
        """
        available_paths = [
            path for path in self.all_paths if
            drone.current_hub in path["path"]
            ]
        if available_paths == None:
            raise DroneCantMove("No available paths")

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
            print("Available connection: ", path["available_connection"])
            print("Available space:      ", path["available_space"])

        valid_paths = [
            p for p in evaluated_paths
            if p["available_space"] and p["available_connection"]
        ]

        if not valid_paths:
            raise DroneCantMove("ERROR: next hub does not have enough room or links availabe")

        priority_choices = [
            p for p in valid_paths if p["priority_next"]
        ]
        final_choices = priority_choices if priority_choices else valid_paths
        chosen_path = min(final_choices, key=lambda p: p["total_turns"])
        drone.destination = chosen_path["next_hub"]
        drone.remaining_turns = chosen_path["total_turns"]
    
    @staticmethod
    def _set_link(a: Hub, b: Hub, add: bool) -> None:
        """
        """
        mod = 1 if add == True else -1
        for link in a.links:
            if link['target_hub'] == b:
                link['incoming_drones'] += mod
        for link in b.links:
            if link['target_hub'] == a:
                link['incoming_drones'] += mod


    def _take_off(self, drone: Drone) -> None:
        """
        """

        drone.current_hub.drone_bay.remove(drone)
        self._set_link(drone.current_hub, drone.destination, True)
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
            DroneStatus.DELIVERED if drone.current_hub.hub_type == "end_hub"
            else DroneStatus.ARRIVED
        )
        if drone.status == DroneStatus.DELIVERED:
            self.drones_left.remove(drone)
        elif drone.status == DroneStatus.ARRIVED:
            self.drones_in_motion.remove(drone)

        self._set_link(drone.current_hub, drone.visited_hubs[-1], False)
        
        drone.visited_hubs.append(drone.current_hub)


    def _simulate_turn(self) -> None:
        """
        """
        self.turn_num += 1

        print(f"Drones left: {[d.id for d in self.drones_left]}")

        available_drones = []
        for drone in self.drones_left:
            if drone.status == DroneStatus.RESTRICTED_FLIGHT:
                drone.status = DroneStatus.FLYING
                continue
            drone.status = DroneStatus.STANDBY
            available_drones.append(drone)

        print(f"Available drones: {[d.id for d in available_drones]}")        
        available_drones.sort(key=lambda p: p.remaining_turns, reverse=True)
        
        while available_drones:
            try:
                fewer_turns = available_drones.pop()
                print(self._get_dron_info(fewer_turns))
                self._flight_planner(fewer_turns)
                self._take_off(fewer_turns)
                print(self._get_dron_info(fewer_turns))
                print(f"Drones left: {[d.id for d in self.drones_left]}")

            except (IndexError, DroneCantMove) as e:
                print(e)
                continue


        print(self._output_turn())

        for drone in self.drones_in_motion:
            if drone.status == DroneStatus.FLYING:
                self._arrive(drone)
        
    
    def start_simulation(self) -> None:
        """
        """
        print(f"Starting drones: {[d.id for d in self.drones_left]}")
        for _ in range(10):
            print(f"TURN: {self.turn_num:03d}")
            self._simulate_turn()
            print()
    
    def _output_turn(self) -> str:
        """
        """
        drone_strings = []
        for drone in self.drones_in_motion:
            string = (
                f"{drone.id}-"
                f"{drone.destination.name}"
                )
            drone_strings.append(string)
        
        return " ".join(drone_strings)
    
    def _get_dron_info(self, drone: Drone) -> str:
        """
        """
        return (
            f"{drone.id} STATUS: {drone.status.name}\n"
            f"  - current position: {drone.current_hub.name if drone.current_hub else "flying"}\n"
            f"  - destination:      {drone.destination.name if drone.destination else "on hold"}\n"
        )
