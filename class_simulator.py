from class_network import Network, Hub, Path, Drone
from class_network import DroneStatus, Zone, HubType
from utils import ERROR, WARNING, STATUS, path_id_generator
import utils
from typing import List, Dict, Set, Generator, Any, Optional
from time import sleep


class HubFullError(Exception):
    pass


class NoLinksAvailableError(Exception):
    pass


class DroneCantMove(Exception):
    pass


class Simulator:
    """Handles the main simulation logic and state for the drone network.

    Args:
        net (Network): Network object containing hubs and links.
    """

    def __init__(self, net: Network) -> None:
        self.net = net
        self.drones_left: List[Drone] = [
            d for d in self.net.start_hub.drone_bay
        ]
        self.drones_in_motion: List[Drone] = []
        self.delivered_drones: List[Drone] = []
        self.all_paths: List[Path] = self._find_all_paths()

        if not self.all_paths:
            raise ValueError(ERROR["critical"]["no_valid_paths"])

        min_turns = min([path.turns_to_finish for path in self.all_paths])
        for drone in self.drones_left:
            drone.remaining_turns = min_turns
            drone.visited_hubs.append(self.net.start_hub)

        self.metrics: Dict[str, Any] = {
            "current_turn": 0,
            "turn": [],
            "avg_turns_per_drone": 0,
            "total_path_cost": 0,
        }

        try:
            with open("output_file.txt", "w"):
                pass

        except FileNotFoundError:
            pass

    def _find_all_paths(
        self,
        start: Optional[Hub] = None,
        visited: Optional[Set[str]] = None,
        current_path: Optional[List[Hub]] = None,
        all_paths: Optional[List[Path]] = None,
    ) -> List[Path]:
        """Recursively finds all valid paths from a starting hub to the end.

        Args:
            start (Hub, optional): Current hub being evaluated.
            visited (Set[Hub], optional): Visited hubs to prevent loops.
            current_path (List[Hub], optional): Current hub sequence.
            all_paths (List[List[Hub]], optional): Found valid paths.

        Returns:
            List[Path]: All possible Path objects linking start and end points.
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

        try:
            if start == self.net.end_hub:
                path = Path(next(path_id_generator), list(current_path))
                if not path.hubs_on_route:
                    raise ValueError(ERROR["path"]["empty_route"])
                first_hub = path.hubs_on_route[0]
                if first_hub is None:
                    raise ValueError(ERROR["path"]["first_hub_none"])
                path._path_status(first_hub)
                all_paths.append(path)
            else:
                for link in start.links:
                    if link["target_hub"].zone == Zone.BLOCKED:
                        continue
                    if link["target_hub"].name not in visited:
                        self._find_all_paths(
                            link["target_hub"],
                            visited,
                            current_path,
                            all_paths
                        )
        except ValueError:
            pass

        current_path.pop()
        visited.remove(start.name)

        return all_paths

    def _flight_planner(self, drone: Drone) -> None:
        """Plans the next flight path for a drone based on available routes.

        Args:
            drone (Drone): Drone requiring flight path evaluation.

        Raises:
            DroneCantMove: If no paths exist or routes are blocked.
            HubFullError: If destination hubs are at maximum capacity.
            NoLinksAvailableError: If no link connection capacity remains.
        """
        available_paths = {
            p for p in self.all_paths if drone.current_hub in p.hubs_on_route
        }
        if available_paths is None:
            raise DroneCantMove(
                ERROR["critical"]["no_available_paths"].format(
                    drone_id=drone.id
                )
            )

        evaluated_paths = set()
        for path_template in available_paths:
            path = Path(path_template.id, path_template.hubs_on_route.copy())
            path._path_status(drone.current_hub)
            evaluated_paths.add(path)

        space_paths = {p for p in evaluated_paths if p.available_space}
        if not space_paths:
            raise HubFullError(WARNING["simulator"]["hub_full"])

        link_paths = {p for p in evaluated_paths if p.available_links}
        if not link_paths:
            raise NoLinksAvailableError(WARNING["simulator"]["no_links"])

        valid_paths = space_paths.intersection(link_paths)
        if not valid_paths:
            raise DroneCantMove(WARNING["simulator"]["path_blocked"])

        min_turns = min(p.turns_to_finish for p in valid_paths)
        shorter_paths = {
            p for p in valid_paths if p.turns_to_finish == min_turns
        }
        priority_paths = {p for p in shorter_paths if p.priority_next}
        chosen_path = (
            priority_paths.pop() if priority_paths else shorter_paths.pop()
        )
        drone.current_path = chosen_path
        drone.destination = chosen_path.next_hub
        drone.remaining_turns = chosen_path.turns_to_finish

    @staticmethod
    def _set_link(
            origin: Optional[Hub], dest: Optional[Hub], add: bool) -> None:
        """Modifies traffic counters for the link between two given hubs.

        Args:
            origin (Hub): Hub from which the drone is departing.
            dest (Hub): Destination hub the drone is heading to.
            add (bool): True to increment usage, False to decrement.
        """
        if not origin or not dest:
            return

        mod = 1 if add is True else -1
        for link in origin.links:
            if link["target_hub"] == dest:
                link["leaving_drones"] += mod
        for link in dest.links:
            if link["target_hub"] == origin:
                link["incoming_drones"] += mod

    def simulate_turn(self) -> Generator[Dict[str, str], None, None]:
        """Generator that emits progressive events during each turn.

        Yields:
            Dict[str, str]: Contains event types and descriptive messages
            for progressive GUI updates.
        """
        available_drones = []

        for drone in self.drones_left:
            if drone in self.drones_in_motion:
                dest = (
                    drone.destination.name if drone.destination else "Unknown"
                )
                yield {
                    "type": "drone_status",
                    "msg": STATUS["drone_flying_restricted"].format(
                        drone_id=drone.id, destination=dest
                    ),
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
                    "msg": STATUS["drone_evaluating"].format(
                        drone_id=lead_drone.id
                    ),
                }

                self._flight_planner(lead_drone)
                self._set_link(
                    lead_drone.current_hub, lead_drone.destination, True
                )
                lead_drone.origin = lead_drone.current_hub
                dest = (
                    lead_drone.destination.name
                    if lead_drone.destination else "Unknown"
                )
                yield {
                    "type": "drone_status",
                    "msg": STATUS["drone_flying"].format(
                        drone_id=lead_drone.id,
                        destination=dest,
                    ),
                }

                lead_drone._take_off()
                self.drones_in_motion.append(lead_drone)

            except (
                IndexError,
                DroneCantMove,
                HubFullError,
                NoLinksAvailableError,
            ) as e:
                yield {
                    "type": "drone_status",
                    "msg": (
                        WARNING["simulator"]["dynamic_drone_warning"].format(
                            drone_id=lead_drone.id, message=str(e))
                        )
                }
                continue

        output = self._output_turn()

        self.metrics["turn"].append(
            {
                "turn_num": int(self.metrics["current_turn"]),
                "drones_moved": int(len(self.drones_in_motion)),
            }
        )

        for drone in list(self.drones_in_motion):
            if drone.status == DroneStatus.FLYING:
                drone._arrive()
                self.drones_in_motion.remove(drone)
                self._set_link(drone.origin, drone.current_hub, False)

                if drone.current_hub:
                    if drone.current_hub.hub_type == HubType.END:
                        yield {
                            "type": "drone_status",
                            "msg": STATUS["drone_delivered"].format(
                                drone_id=drone.id
                            ),
                        }
                        self.drones_left.remove(drone)
                        self.delivered_drones.append(drone)

                    else:
                        dest = (
                            drone.current_hub.name
                            if drone.current_hub else "Unknown"
                        )
                        yield {
                            "type": "drone_status",
                            "msg": STATUS["drone_arrived"].format(
                                drone_id=drone.id, hub_name=dest
                            ),
                        }

        self.metrics["current_turn"] += 1

        yield {"type": "end_turn", "msg": output}
        sleep(utils.PACE * 3)

    def _output_turn(self) -> str:
        """Generates text output for a single simulation turn.

        Returns:
            str: Formatted string detailing active drone movements.
        """
        drone_strings: List[str] = []

        for drone in self.drones_in_motion:
            if drone.status == DroneStatus.FLYING:
                dest = (
                    drone.destination.name if drone.destination else 'Unknown'
                )
                stat_str = f"{drone.id}-{dest}"

            elif drone.status == DroneStatus.RESTRICTED_FLIGHT:
                origin = (
                    drone.origin.name if drone.origin else 'Unknown'
                )
                dest = (
                    drone.destination.name if drone.destination else 'Unknown'
                )
                stat_str = f"{drone.id}-{origin}-{dest}"

            drone_strings.append(stat_str)

        final_str = " ".join(drone_strings)

        with open("output_file.txt", "a") as out:
            out.write(final_str + "\n")

        return final_str

    def _get_metrics(self) -> None:
        """Calculates and stores final performance metrics after a run."""
        self.metrics["total_path_cost"] = sum(
            [d.total_moves for d in self.delivered_drones]
        )

        if self.metrics["current_turn"] > 0:
            self.metrics["drones_moved_per_turn"] = (
                self.metrics["total_path_cost"]
                / (self.metrics["current_turn"] * self.net.nb_drones)
                * 100
            )
        else:
            self.metrics["drones_moved_per_turn"] = 0

        if self.delivered_drones:
            self.metrics["min_turns"] = min(
                [d.total_moves for d in self.delivered_drones]
            )
            self.metrics["max_turns"] = max(
                [d.total_moves for d in self.delivered_drones]
            )
            self.metrics["avg_turns_per_drone"] = (
                self.metrics["total_path_cost"] / len(self.delivered_drones)
            )
        else:
            self.metrics["min_turns"] = 0
            self.metrics["max_turns"] = 0
            self.metrics["avg_turns_per_drone"] = 0
