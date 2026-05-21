from pydantic import BaseModel, Field, ValidationError, model_validator, ConfigDict, ConfigDict
from typing import Protocol, Literal, Optional, Tuple, Any, List, Dict, ClassVar
from utils import UX, STATUS, ERROR
from enum import Enum
import sys


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


class Drone(BaseModel):
    """
    """
    id: str
    status: DroneStatus
    current_hub: Optional[Hub] = Field(default=None)
    destination: Optional[Hub] = Field(default=None)
    visited_hubs: List[Hub] = Field(default_factory=list)
    remaining_turns: int = Field(default=None)


class Hub(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    """
    Parses hub information from raw data
    """
    hub_type: Literal['start_hub', 'hub', 'end_hub']
    name: str = Field(pattern=r"^[^- ]*$")
    coords: Tuple[int, int] = Field(default_factory=tuple)
    color: Optional[str] = Field(default=None, pattern=r"^[^ ]*$")
    max_drones: Optional[int] = Field(default=1, ge=1)
    zone: Optional[Zone] = Zone.NORMAL
    links: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    drone_bay: Optional[List[Drone]] = Field(default_factory=list)


class Network(BaseModel):
    """
    ...
    """
    map: str
    nb_drones: int = Field(ge=1)
    start_hub: Hub
    hub: List[Hub] = Field(default_factory=list)
    end_hub: Hub
    connections: List[Dict]
    
    @model_validator(mode='after')
    def validator(self) -> 'Network':
        """
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
                     'incoming_drones': 0}
                    )
                hub_b.links.append(
                    {'target_hub': hub_a,
                     'max': max_link_capacity,
                     'incoming_drones': 0}
                    )
            
            for drone in self.start_hub.drone_bay:
                drone.current_hub = self.start_hub
        
        print(' OK')
        return self
    
    def get_map_info(self) -> str:
        """
        """
        data = f"  - nb_drones: {self.nb_drones}\n"
        data += f"  - hub list:\n"
        for h in self.hub:
            data += f"    · {h.name}\n"
            data += f"        coords: {h.coords}\n"
            if h.color:
                data += f"        color: {h.color}\n"
            if h.zone:
                data += f"        zone: {h.zone.value}\n"
            if h.max_drones:
                data += f"        max_drones: {h.max_drones}\n"
        data += f"  - links:\n"
        for c in self.connections:
            data += f"    · {c["point_a"]} - {c["point_b"]}"
            data += (
                " [max_link_capacity="
                f"{c.get("max_link_capacity",1)}]\n"
                )
        
        return data
