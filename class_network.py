from pydantic import BaseModel, Field, model_validator, ConfigDict
from typing import Optional, Tuple, Any, List, Dict, Union
from utils import ERROR
from enum import Enum
from pydantic_core import PydanticCustomError


class Zone(Enum):
    NORMAL = "normal"
    BLOCKED = "blocked"
    RESTRICTED = "restricted"
    PRIORITY = "priority"


class DroneStatus(Enum):
    STANDBY = "standby"
    FLYING = "flying"
    RESTRICTED_FLIGHT = "restricted_flight"
    ARRIVED = "arrived"
    DELIVERED = "delivered"


class HubType(Enum):
    START = "start_hub"
    HUB = "hub"
    END = "end_hub"


class Hub(BaseModel):
    """Represents a Hub node with coordinates and logic variables."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    hub_type: HubType
    name: str = Field(pattern=r"^[^- ]*$")
    coords: Tuple[int, int]
    color: Optional[str] = Field(default=None, pattern=r"^[^ ]*$")
    max_drones: int = Field(default=1, ge=1)
    zone: Zone = Field(default=Zone.NORMAL)
    links: List[Dict[str, Any]] = Field(default_factory=list)
    drone_bay: List["Drone"] = Field(default_factory=list)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Hub):
            return False
        return self.name == other.name

    def __hash__(self) -> int:
        return hash(self.name)


class Path:
    """Defines a navigable sequence of linked hubs across the network.

    Args:
        id (Union[int, str]): A logical identifier for routing.
        hubs_on_route (List[Hub]): Sequence of hubs in this Path.
    """

    def __init__(self, id: Union[int, str], hubs_on_route: List[Hub]) -> None:
        if isinstance(id, str):
            self.id = id
        if isinstance(id, int):
            self.id = f"route_{id:03d}"
        self.hubs_on_route = hubs_on_route

    def _path_status(self, current_hub: Optional[Hub]) -> None:
        """Updates path variables based on the active drone position.

        Args:
            current_hub (Hub): The current geographic placement.
        """
        if current_hub is None:
            return

        hub_index = self.hubs_on_route.index(current_hub)
        self.hubs_on_route = self.hubs_on_route[hub_index:]
        self.next_hub = self.hubs_on_route[1]
        self.turns_to_finish = int(
            len([hub for hub in self.hubs_on_route])
            + len(
                [
                    hub
                    for hub in self.hubs_on_route
                    if hub.zone == Zone.RESTRICTED
                ]
            )
            - 1
        )
        self.priority_next = (
            True if self.next_hub.zone == Zone.PRIORITY else False
        )
        self.available_space, self.available_links = self._is_hub_accessible()

    def _is_hub_accessible(self) -> Tuple[bool, bool]:
        """Checks space and link availability of the next destination.

        Returns:
            Tuple[bool, bool]: Available volume space and link capacity.
        """
        origin = self.hubs_on_route[0]
        dest = self.hubs_on_route[1]
        available_space = False
        available_links = False
        total_incoming = 0

        for link in dest.links:
            total_incoming += link["incoming_drones"]
            if link["target_hub"] == origin:
                if (
                    link["max"]
                    > link["incoming_drones"] + link["leaving_drones"]
                ):
                    available_links = True

        free_space = dest.max_drones - len(dest.drone_bay)
        if free_space > total_incoming:
            available_space = True

        return (available_space, available_links)

    def __eq__(self, other: Any) -> bool:
        """Evaluates path equality based on ID and route length.

        Args:
            other (object): Comparable item evaluating equality.

        Returns:
            bool: True if IDs and route lengths match.
        """
        if not isinstance(other, Path):
            return False
        return (
            self.id == other.id
            and self.turns_to_finish == other.turns_to_finish
        )

    def __hash__(self) -> int:
        """Generates a unique hash key mapped to ID and route length.

        Returns:
            int: Computed hash key value.
        """
        return hash((self.id, self.turns_to_finish))


class Drone(BaseModel):
    """Logical entity encapsulating drone navigation and properties."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: str
    status: DroneStatus
    remaining_turns: int = Field(default=0)
    current_path: Optional[Path] = Field(default=None)
    current_hub: Optional[Hub] = Field(default=None)
    origin: Optional[Hub] = Field(default=None)
    destination: Optional[Hub] = Field(default=None)
    visited_hubs: List[Hub] = Field(default_factory=list)
    total_moves: int = Field(default=0)

    def _take_off(self) -> None:
        """Initiates flight by removing drone from bay and updating status."""
        if self.current_hub is None:
            raise ValueError(ERROR["drone"]["take_off_none_hub"])
        self.current_hub.drone_bay.remove(self)
        self.current_hub = None
        if self.destination is None:
            raise ValueError(ERROR["drone"]["take_off_no_destination"])
        if self.destination.zone == Zone.RESTRICTED:
            self.status = DroneStatus.RESTRICTED_FLIGHT
        else:
            self.status = DroneStatus.FLYING
        self.total_moves += 1

    def _arrive(self) -> None:
        """Registers the drone inside the destination node."""
        if self.destination is None:
            raise ValueError(ERROR["drone"]["arrive_none_hub"])
        if self.destination.hub_type != HubType.END:
            self.destination.drone_bay.append(self)
        self.current_hub = self.destination
        self.destination = None
        self.status = (
            DroneStatus.DELIVERED
            if self.current_hub.hub_type == HubType.END
            else DroneStatus.ARRIVED
        )
        self.visited_hubs.append(self.current_hub)

        if self.current_path and self.status == DroneStatus.ARRIVED:
            if self.current_hub is None:
                raise ValueError(
                    ERROR["drone"]["current_hub_none_path_status"]
                    )
            self.current_path._path_status(self.current_hub)
            self.remaining_turns = self.current_path.turns_to_finish


class Network(BaseModel):
    """Validates models to ensure map topology structural integrity."""

    map: str
    nb_drones: int = Field(ge=1)
    start_hub: Hub
    hub: List[Hub] = Field(default_factory=list)
    end_hub: Hub
    connections: List[Dict[str, Any]]

    @model_validator(mode="after")
    def validator(self) -> "Network":
        """Checks the graph for duplicates or invalid links before simulation.

        Returns:
            Network: Formatted active class instance.

        Raises:
            ValueError: Triggered during faulty properties or link states.
        """
        all_hubs = self.hub + [self.start_hub, self.end_hub]
        unique_names = {hub.name for hub in all_hubs}
        if len(all_hubs) != len(unique_names):
            raise PydanticCustomError(
                "duplicate_hub_names",
                ERROR["parser"]["duplicate_hub_names"]
            )

        unique_coords = {hub.coords for hub in all_hubs}
        if len(all_hubs) != len(unique_coords):
            raise PydanticCustomError(
                "duplicate_hub_coords",
                ERROR["parser"]["duplicate_hub_coords"]
            )

        unique_links = set()
        hub_dict = {hub.name: hub for hub in self.hub}
        hub_dict[self.start_hub.name] = self.start_hub
        hub_dict[self.end_hub.name] = self.end_hub
        for link in self.connections:
            current_link = tuple(sorted((link["point_a"], link["point_b"])))
            if current_link in unique_links:
                raise PydanticCustomError(
                    "duplicate_link",
                    ERROR["parser"]["duplicate_link"].format(
                        point_a=link["point_a"], point_b=link["point_b"]
                    )
                )
            unique_links.add(current_link)

            if link["point_a"] == link["point_b"]:
                raise PydanticCustomError(
                    "self_link",
                    ERROR["parser"]["self_link"].format(
                        point_a=link["point_a"], point_b=link["point_b"]
                    )
                )

            for point in [link["point_a"], link["point_b"]]:
                if point not in unique_names:
                    raise PydanticCustomError(
                        "missing_hub",
                        ERROR["parser"]["missing_hub"].format(point=point)
                    )

            hub_a = hub_dict.get(link["point_a"])
            hub_b = hub_dict.get(link["point_b"])

            max_link_capacity = link.get("max_link_capacity", 1)
            if max_link_capacity < 1:
                raise PydanticCustomError(
                    "invalid_max_link_capacity",
                    ERROR["parser"]["invalid_max_link_capacity"]
                )

            if hub_a and hub_b:
                hub_a.links.append(
                    {
                        "target_hub": hub_b,
                        "max": max_link_capacity,
                        "incoming_drones": 0,
                        "leaving_drones": 0,
                    }
                )
                hub_b.links.append(
                    {
                        "target_hub": hub_a,
                        "max": max_link_capacity,
                        "incoming_drones": 0,
                        "leaving_drones": 0,
                    }
                )

            for drone in self.start_hub.drone_bay:
                drone.current_hub = self.start_hub

        return self
