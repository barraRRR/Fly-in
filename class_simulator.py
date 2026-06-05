from class_network import Network, Hub, Path, Drone, DroneStatus, Zone
from copy import copy
from utils import ERROR, WARNING, STATUS, DELAY, path_id_generator
import utils
from typing import List, Dict, Set, Tuple, Generator
from time import sleep


class HubFullError(Exception):
    pass


class NoLinksAvailableError(Exception):
    pass


class DroneCantMove(Exception):
    pass


class Simulator:
    """
    """
    def __init__(self, net: Network) -> None:
        self.net = net
        self.turn_num: int = 0
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
            ) -> List[Path]:
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
                ERROR['critical']['no_available_paths'].format(
                drone_id=drone.id
            ))

        evaluated_paths = set()
        for path_template in available_paths:
            path = Path(path_template.id, path_template.hubs_on_route.copy())
            path._path_status(drone.current_hub)
            evaluated_paths.add(path)

        space_paths = {p for p in evaluated_paths if p.available_space}
        if not space_paths:
            raise HubFullError(WARNING['simulator']['hub_full'])
                               
        link_paths = {p for p in evaluated_paths if p.available_links}
        if not link_paths:
            raise NoLinksAvailableError(
                WARNING['simulator']['no_links']
                )
        
        valid_paths = space_paths.intersection(link_paths)
        if not valid_paths:
            raise DroneCantMove(WARNING['simulator']['path_blocked'])

        priority_paths = {p for p in valid_paths if p.priority_next}
        shortlist = priority_paths if priority_paths else valid_paths
        chosen_path = min(shortlist, key=lambda p: p.turns_to_finish)
        drone.current_path = chosen_path
        drone.destination = chosen_path.next_hub
        drone.remaining_turns = chosen_path.turns_to_finish
    
    @staticmethod
    def _set_link(origin: Hub, dest: Hub, add: bool) -> None:
        """
        """
        mod = 1 if add == True else -1
        for link in origin.links:
            if link['target_hub'] == dest:
                link['leaving_drones'] += mod
        for link in dest.links:
            if link['target_hub'] == origin:
                link['incoming_drones'] += mod

    def simulate_turn(self) -> Generator[Dict[str, str], None, None]:
        """
        Generador que emite eventos durante cada turno.
        Permite que la GUI se actualice progresivamente sin bloqueos.
        """
        available_drones = []
        
        for drone in self.drones_left:
            if drone in self.drones_in_motion:
                yield {
                    "type": "drone_status",
                    "msg": STATUS['drone_flying_restricted'].format(
                        drone_id=drone.id, 
                        destination=drone.destination.name
                    )
                }
                drone.status = DroneStatus.FLYING
                continue
            drone.status = DroneStatus.STANDBY
            available_drones.append(drone)

        available_drones.sort(key=lambda p: p.id, reverse=True)
        available_drones.sort(key=lambda p: p.remaining_turns, reverse=True)

        while available_drones:
            try:
                lead_drone = available_drones.pop()
                
                yield {
                    "type": "drone_status",
                    "msg": STATUS['drone_evaluating'].format(drone_id=lead_drone.id)
                }
                
                self._flight_planner(lead_drone)
                self._set_link(
                    lead_drone.current_hub, lead_drone.destination, True
                )
                lead_drone.origin = lead_drone.current_hub
                
                yield {
                    "type": "drone_status",
                    "msg": STATUS['drone_flying'].format(
                        drone_id=lead_drone.id,
                        destination=lead_drone.destination.name
                    )
                }
                
                lead_drone._take_off()
                self.drones_in_motion.append(lead_drone)
    
            except (
                IndexError, DroneCantMove,
                HubFullError, NoLinksAvailableError
            ) as e:
                yield {
                    "type": "drone_status",
                    "msg": f"{lead_drone.id} [WARNING]: {str(e)}"
                }
                continue

        output = self._output_turn()

        for drone in list(self.drones_in_motion):
            if drone.status == DroneStatus.FLYING:
                drone._arrive()
                self.drones_in_motion.remove(drone)
                self._set_link(drone.origin, drone.current_hub, False)
                
                if drone.status == DroneStatus.DELIVERED:
                    yield {
                        "type": "drone_status",
                        "msg": STATUS['drone_delivered'].format(drone_id=drone.id)
                    }
                    self.drones_left.remove(drone)
                
                else:
                    yield {
                    "type": "drone_status",
                    "msg": f"{drone.id} [ARRIVED]: Reached {drone.current_hub.name}"
                    }
        
        self.turn_num += 1
        
        yield {
            "type": "end_turn",
            "msg": output
        }
        sleep(utils.PACE * 3)
    
    def _output_turn(self) -> str:
        """
        """
        drone_strings = [
            f"{drone.id}-{drone.destination.name}"
            for drone in self.drones_in_motion
            ]
        final_str = " ".join(drone_strings)

        with open("output_file.txt", "a") as out:
            out.write(final_str + "\n")
        
        return final_str
