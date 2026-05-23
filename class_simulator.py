from class_network import Network, Hub, Path, Drone, DroneStatus, Zone
from class_parser import MapParser
from copy import deepcopy
from utils import ERROR, path_id_generator
from typing import List, Dict, Set, Tuple



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
        self.net = Network(**self.map.data)
        self.drones_left: List[Drone] = [
            d for d in self.net.start_hub.drone_bay
            ]
        self.drones_in_motion: List[Drone] = []
        self.all_paths: List[Path] = self._find_all_paths()

        min_turns = min([path.turns_to_finish for path in self.all_paths])
        for drone in self.drones_left:
            drone.remaining_turns = min_turns
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
            path = Path(next(path_id_generator), list(current_path))
            path._path_status(path.hubs_on_route[0])
            all_paths.append(path)
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
    
    def _flight_planner(self, drone: Drone) -> None:
        """
        """
        available_paths = {
            p for p in self.all_paths if
            drone.current_hub in p.hubs_on_route
        }
        if available_paths == None:
            raise DroneCantMove(
                ERROR['simulator']['no_available_paths'].format(
                drone_id=drone.id
            ))

        evaluated_paths = set()
        for path_template in available_paths:
            path = deepcopy(path_template)
            path._path_status(drone.current_hub)
            evaluated_paths.add(path)

        space_paths = {p for p in evaluated_paths if p.available_space}
        if not space_paths:
            raise HubFullError(ERROR['simulator']['hub_full_error'])
                               
        link_paths = {p for p in evaluated_paths if p.available_links}
        if not link_paths:
            raise NoLinksAvailableError(
                ERROR['simulator']['no_links_available']
                )
        
        valid_paths = space_paths.intersection(link_paths)
        if not valid_paths:
            raise DroneCantMove(ERROR['simulator']['drone_cant_move'])

        priority_paths = {p for p in valid_paths if p.priority_next}
        shortlist = priority_paths if priority_paths else valid_paths
        chosen_path = min(shortlist, key=lambda p: p.turns_to_finish)
        drone.current_path = chosen_path
        drone.destination = chosen_path.next_hub
        drone.remaining_turns = chosen_path.turns_to_finish
    
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

    def _simulate_turn(self) -> None:
        """
        """
        available_drones = []
        for drone in self.drones_left:
            if drone in self.drones_in_motion:
                drone.status = DroneStatus.FLYING
                continue
            drone.status = DroneStatus.STANDBY
            available_drones.append(drone)

        available_drones.sort(key=lambda p: p.remaining_turns, reverse=True)

        while available_drones:
            try:
                lead_drone = available_drones.pop()
                self._flight_planner(lead_drone)
                self._set_link(
                    lead_drone.current_hub, lead_drone.destination, True
                    )
                lead_drone.origin = lead_drone.current_hub
                lead_drone._take_off()
                self.drones_in_motion.append(lead_drone)
    
            except (
                IndexError, DroneCantMove,
                HubFullError, NoLinksAvailableError
                ) as e:
                print(e)
                continue

        print(self._output_turn())

        for drone in list(self.drones_in_motion):
            if drone.status == DroneStatus.FLYING:
                drone._arrive()
                self.drones_in_motion.remove(drone)
                self._set_link(
                    drone.origin, drone.current_hub, False
                    )
                if drone.status == DroneStatus.DELIVERED:
                    self.drones_left.remove(drone)

    def start_simulation(self) -> None:
        """
        """
        iterations = 0
        while self.drones_left:
            self.turn_num += 1
            iterations += 1
            print(f"TURN: {self.turn_num:03d}")
            self._simulate_turn()
            print()
            if iterations > 10:
                print(f"ERROR: Bucle infinito en available_drones. Drones restantes: {len(self.drones_left)}")
                break
        print(f"Total turns: {self.turn_num}")
    
    def _output_turn(self) -> str:
        """
        """
        drone_strings = []
        for drone in self.drones_in_motion:
            string = (
                f"{drone.id}-"
                f"{drone.destination.name if drone.destination
                   else "on hold"}"
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
            f"  - remaining turns:  {drone.remaining_turns}\n"
        )
