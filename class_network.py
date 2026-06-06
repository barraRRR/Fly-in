from pydantic import BaseModel, Field, model_validator, ConfigDict
from typing import Optional, Tuple, Any, List, Dict, Union
from utils import ERROR
from enum import Enum


class Zone(Enum):

    NORMAL = 'normal'
    BLOCKED = 'blocked'
    RESTRICTED = 'restricted'
    PRIORITY = 'priority'


class DroneStatus(Enum):
    
    STANDBY = 'standby'
    FLYING = 'flying'
    RESTRICTED_FLIGHT = 'restricted_flight'
    ARRIVED = 'arrived'
    DELIVERED = 'delivered'

class HubType(Enum):

    START = 'start_hub'
    HUB = 'hub'
    END = 'end_hub'


class Hub(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    """Represents a geographic Hub node in the structural network
    containing coordinate constraints and logic variables.
    """
    hub_type: HubType
    name: str = Field(pattern=r"^[^- ]*$")
    coords: Tuple[int, int] = Field(default_factory=tuple)
    color: Optional[str] = Field(default=None, pattern=r"^[^ ]*$")
    max_drones: Optional[int] = Field(default=1, ge=1)
    zone: Optional[Zone] = Zone.NORMAL
    links: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    drone_bay: Optional[List['Drone']] = Field(default_factory=list)

    def __eq__(self, other):
        if not isinstance(other, Hub):
            return False
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)


class Path:
    """Defines a navigable route (sequence of linked hubs) mapped across the network.

    Args:
        id (Union[int, str]): A logical identifier for routing purposes.
        hubs_on_route (List[Hub]): The progressive sequence of hubs
            completing this Path.
    """
    def __init__(self, id: Union[int, str], hubs_on_route: List[Hub]) -> None:
        if isinstance(id, str):
            self.id = id
        if isinstance(id, int):
            self.id = f"route_{id:03d}"
        self.hubs_on_route = hubs_on_route
    
    def _path_status(self,
                      current_hub: Hub) -> None:
        """Updates path variables dynamically dependent on the provided
        active position of a navigating drone.

        Args:
            current_hub (Hub): The current geographic placement.
        """
        hub_index = self.hubs_on_route.index(current_hub)
        self.hubs_on_route = self.hubs_on_route[hub_index:]
        self.next_hub = self.hubs_on_route[1]
        self.turns_to_finish = (int(
            len([hub for hub in self.hubs_on_route]) +
            len([hub for hub in self.hubs_on_route if
                 hub.zone == Zone.RESTRICTED]) - 1)
        )
        self.priority_next = (
            True if self.next_hub.zone == Zone.PRIORITY else False
        )
        self.available_space, self.available_links = self._is_hub_accessible()
    
    def _is_hub_accessible(self) -> Tuple[bool, bool]:
        """Determines accessibility of the immediate next destination hub
        regarding constraints.

        Returns:
            Tuple[bool, bool]: A pair representing (available volume space,
                available linking capacity).
        """
        origin = self.hubs_on_route[0]
        dest = self.hubs_on_route[1]
        available_space = False
        available_links = False
        total_incoming = 0

        for link in dest.links:
            total_incoming += link["incoming_drones"]
            if link['target_hub'] == origin:
                if (link['max'] > link['incoming_drones'] +
                        link['leaving_drones']):
                    available_links = True

        free_space = dest.max_drones - len(dest.drone_bay)
        if free_space > total_incoming:
            available_space = True

        return (available_space, available_links)
    
    def _block_priority_traps() -> None:
        """TODO: Detects and locks network paths evaluated as potential
        dead-end priority traps.
        """
        ...

    def __eq__(self, other):
        """Defines strict path equality prioritizing unique IDs alongside
        computational route finish lengths.

        Args:
            other (object): Comparable item evaluating equality.

        Returns:
            bool: True natively evaluating equivalence if both constraints
                align accurately.
        """
        if not isinstance(other, Path):
            return False
        return (
            self.id == other.id and
            self.turns_to_finish == other.turns_to_finish
        )
    
    def __hash__(self):
        """Generates a reliable unique hash key strictly bounded to unique
        IDs mapping.

        Returns:
            int: Immutable computed hash key value mapping id mapping combined
                against total computational lengths.
        """
        return hash((self.id, self.turns_to_finish))


class Drone(BaseModel):
    """Logical entity encapsulating navigation flags, active coordinate
    tracking, and movement properties across a turn sequence.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: str
    status: DroneStatus
    remaining_turns: int = Field(default=0)
    current_path: Path = Field(default=None)
    current_hub: Optional[Hub] = Field(default=None)
    origin: Optional[Hub] = Field(default=None)
    destination: Optional[Hub] = Field(default=None)
    visited_hubs: List[Hub] = Field(default_factory=list)
    total_moves: int = Field(default=0)

    def _take_off(self) -> None:
        """Disconnects the Drone logically from a local bay allowing
        simulated flight initiation while toggling status triggers.
        """
        self.current_hub.drone_bay.remove(self)
        self.current_hub = None
        if self.destination.zone == Zone.RESTRICTED:
            self.status = DroneStatus.RESTRICTED_FLIGHT
        else:
            self.status = DroneStatus.FLYING
        self.total_moves += 1

    def _arrive(self) -> None:
        """Registers the drone inside a previously initialized destination
        node establishing new location configurations cleanly.
        """
        if self.destination.hub_type != HubType.END:
            self.destination.drone_bay.append(self)
        self.current_hub = self.destination
        self.destination = None
        self.status = (
            DroneStatus.DELIVERED if self.current_hub.hub_type == HubType.END
            else DroneStatus.ARRIVED
        )        
        self.visited_hubs.append(self.current_hub)

        if self.current_path and self.status == DroneStatus.ARRIVED:
            self.current_path._path_status(self.current_hub)
            self.remaining_turns = self.current_path.turns_to_finish

    
class Network(BaseModel):
    """Encapsulates mapped file inputs binding validation models to ensure
    structural integrity over the map parsing execution layer.
    """
    map: str
    nb_drones: int = Field(ge=1)
    start_hub: Hub
    hub: List[Hub] = Field(default_factory=list)
    end_hub: Hub
    connections: List[Dict]
    
    @model_validator(mode='after')
    def validator(self) -> 'Network':
        """Checks the topological graph for duplications, invalid links, or
        invalid constraints strictly before launching any simulator objects.

        Returns:
            Network: Returning the properly formatted active class instance
                resolving success states.

        Raises:
            ValueError: Detailed mapping to ERROR JSON formats triggered
                during faulty duplicate properties/link states.
        """
        all_hubs = self.hub + [self.start_hub, self.end_hub]
        unique_names = {hub.name for hub in all_hubs}
        if len(self.hub) > len(unique_names):
            raise ValueError(ERROR['parser']['duplicate_hub_names'])

        unique_coords = {hub.coords for hub in self.hub}
        if len(self.hub) > len(unique_coords):
            raise ValueError(ERROR['parser']['duplicate_hub_coords'])

        unique_links = set()
        hub_dict = {hub.name: hub for hub in self.hub}
        hub_dict[self.start_hub.name] = self.start_hub
        hub_dict[self.end_hub.name] = self.end_hub
        for link in self.connections:
            current_link = tuple(sorted(
                (link["point_a"], link["point_b"])
                ))
            if current_link in unique_links:
                raise ValueError(ERROR['parser']['duplicate_link'])
            unique_links.add(current_link)

            if link["point_a"] == link["point_b"]:
                raise ValueError(
                    ERROR['parser']['self_link'].format(
                        point_a=link["point_a"],
                        point_b=link["point_b"])
                        )

            for point in [link["point_a"], link["point_b"]]:
                if point not in unique_names:
                    raise ValueError(ERROR['parser']['missing_hub'].format(
                        point=point
                        ))
            
            hub_a = hub_dict.get(link["point_a"])
            hub_b = hub_dict.get(link["point_b"])

            max_link_capacity = link.get("max_link_capacity", 1)
            if max_link_capacity < 1:
                raise ValueError

            if hub_a and hub_b:
                hub_a.links.append(
                    {'target_hub': hub_b,
                     'max': max_link_capacity,
                     'incoming_drones': 0,
                     'leaving_drones': 0}
                    )
                hub_b.links.append(
                    {'target_hub': hub_a,
                     'max': max_link_capacity,
                     'incoming_drones': 0,
                     'leaving_drones': 0}
                    )

            for drone in self.start_hub.drone_bay:
                drone.current_hub = self.start_hub

        return self