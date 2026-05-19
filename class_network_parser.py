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
    DISPATCHED = 'dispatched'
    TRANSIT = 'transit'
    DELIVERED = 'delivered'


class Parser(Protocol):
    def parse(raw: str) -> None:
        ...


class Drone:
    """
    """
    def __init__(self, code: int) -> None:
        self.id: str = f"FOO_{code:03d}"
        self.status: DroneStatus = DroneStatus.STANDBY


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

    @classmethod
    def parse(cls, line: str) -> 'Hub':
        """
        """
        line = line.lower().strip()
        hub_type, data = line.split(':', 1)
        hub_type = hub_type.strip(' :')
        data = data.strip().split(' ')
        name = data[0]

        x = int(data[1])
        y = int(data[2])

        payload = {
            'hub_type': hub_type,
            'name': name,
            'coords': (x, y),
        }

        try:
            for chunk in data[3:]:
                if '=' not in chunk:
                    raise ValueError('Invalid metadata format')
                meta, value = chunk.split('=')
                meta = meta.strip('[]')
                value = value.strip('[]')
                if meta in ['color', 'max_drones', 'zone']:
                    if meta == 'max_drones':
                        payload[meta] = int(value)
                    else:
                        payload[meta] = value
                else:
                    raise ValueError(ERROR['parser']['metadata'].format(meta=meta))
        
        except IndexError:
            pass
        
        return cls(**payload)
    
    def load_drones(self, nb_drones: int) -> None:
        """
        """
        for i in range(nb_drones):
            new_drone = Drone(i)
            self.drone_bay.append(new_drone)
            

class Connection(BaseModel):
    """
    Parses connection information from raw data
    """
    point_a: str
    point_b: str
    max_link_capacity: Optional[int] = Field(default=1, ge=1)

    @classmethod
    def parse(cls, line: str) -> 'Connection':
        """
        """
        line = line.lower().strip()
        data = line.split(':', 1)[1]
        data = data.strip().split(' ')
        if '-' not in data[0]:
            raise ValueError('Invalid connection format')
        
        point_a, point_b = data[0].split('-')
        payload = {
            'point_a': point_a,
            'point_b': point_b,
        }

        try:
            if '=' not in data[1]:
                raise ValueError('Invalid capacity format')
            
            max_link_capacity = int(data[1].strip('[]').split('=')[1])
            payload['max_link_capacity'] = max_link_capacity
        
        except IndexError:
            pass
        
        return cls(**payload)


class Network(BaseModel):
    """
    ...
    """
    FACTORY: ClassVar[Dict[str, type[Parser]]] = {
        'start_hub': Hub,
        'hub': Hub,
        'end_hub': Hub,
        'connection': Connection
    }
    
    nb_drones: int = Field(ge=1)
    start_hub: Hub
    hub: List[Hub] = Field(default_factory=list)
    end_hub: Hub
    connection: List[Connection] = Field(default_factory=list)

    @classmethod
    def parse(cls, file: str) -> 'Network':
        """
        Opens map and collects raw data
        """
        first_line_nb_drones = False
        payload = {
            'nb_drones': None,
            'start_hub': None,
            'hub': [],
            'end_hub': None,
            'connection': []
        }
        print(STATUS['loading_map'].format(map=file), end='')
        with open(file, 'r') as raw:
            print(' OK')
            print(STATUS['parsing_map'].format(map=file), end='')
            for line in raw:
                clean_line = line.strip()
                if not clean_line or clean_line.startswith('#'):
                    continue

                key, data = clean_line.lower().split(':', 1)
                key = key.strip()
                data = data.strip()
                if not first_line_nb_drones and key != 'nb_drones':
                    raise ValueError(ERROR['parser']['nb_drones_first_item'])
                
                elif first_line_nb_drones and key == 'nb_drones':
                    raise ValueError(ERROR['parser']['nb_drones_repeated'])
                
                elif key == 'nb_drones':
                    payload['nb_drones'] = int(data)
                    first_line_nb_drones = True

                elif key == 'start_hub' and not payload['start_hub']:
                    payload['start_hub'] = cls.FACTORY[key].parse(line)
                    payload['start_hub'].load_drones(payload['nb_drones'])

                elif key == 'end_hub' and not payload['end_hub']:
                    payload['end_hub'] = cls.FACTORY[key].parse(line)

                elif key in ['hub', 'connection']:
                    payload[key].append(cls.FACTORY[key].parse(line))
                
                else:
                    raise ValueError
        
        hub_dict = {hub.name: hub for hub in payload['hub']}
        hub_dict[payload['start_hub'].name] = payload['start_hub']
        hub_dict[payload['end_hub'].name] = payload['end_hub']

        for link in payload['connection']:
            hub_a = hub_dict.get(link.point_a)
            hub_b = hub_dict.get(link.point_b)
            
            if hub_a and hub_b:
                hub_a.links.append(
                    {'edge': hub_b, 'max': link.max_link_capacity}
                    )
                hub_b.links.append(
                    {'edge': hub_a, 'max': link.max_link_capacity}
                    )

        return cls(**payload)
    
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
        
        unique_connections = set()
        for connection in self.connection:
            current_connection = tuple(sorted(
                (connection.point_a, connection.point_b)
                ))
            if current_connection in unique_connections:
                raise ValueError(ERROR['parser']['duplicate_connection'])
            unique_connections.add(current_connection)

            if connection.point_a == connection.point_b:
                raise ValueError(
                    ERROR['parser']['self_link'].format(
                        point_a=connection.point_a,
                        point_b=connection.point_b)
                        )
            
            for point in [connection.point_a, connection.point_b]:
                if point not in unique_names:
                    raise ValueError(ERROR['parser']['missing_hub'].format(
                        point=point
                        ))
        
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
        data += f"  - connections:\n"
        for c in self.connection:
            data += f"    · {c.point_a} - {c.point_b}"
            data += (
                " [max_link_capacity="
                f"{c.max_link_capacity}]\n" if c.max_link_capacity else "\n"
                )
        
        return data
