from pydantic import BaseModel, Field, ValidationError, model_validator
from typing import Dict, List, Tuple, Literal, Optional, Protocol, ClassVar
from utils import UX, STATUS, ERROR
from enum import Enum
import sys


class Zone(Enum):

    NORMAL = 'normal'
    BLOCKED = 'blocked'
    RESTRICTED = 'restricted'
    PRIORITY = 'priority'


class Parser(Protocol):
    def parse(raw: str) -> None:
        ...


class Hub(BaseModel):
    """
    Parses hub information from raw data
    """
    type: Literal['start_hub', 'hub', 'end_hub']
    name: str = Field(pattern=r"^[^- ]*$")
    coords: Tuple[int, int] = Field(default_factory=tuple)
    color: Optional[str] = Field(default=None, pattern=r"^[^ ]*$")
    max_drones: Optional[int] = Field(default=1, ge=1)
    zone: Optional[Zone] = Zone.NORMAL

    @classmethod
    def parse(cls, line: str) -> 'Hub':
        """
        """
        line = line.lower().strip()
        type, data = line.split(':', 1)
        type = type.strip(' :')
        data = data.strip().split(' ')
        name = data[0]

        x = int(data[1])
        y = int(data[2])

        payload = {
            'type': type,
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
            

class Connection(BaseModel):
    """
    Parses connection information from raw data
    """
    point_a: str
    point_b: str
    link: Tuple[str, str] = Field(default_factory=tuple)
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
            'link': (point_a, point_b)
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
    hub: List[Hub] = Field(default_factory=list, min_length=2)
    connection: List[Connection] = Field(default_factory=list)

    @classmethod
    def parser(cls, file: str) -> 'Network':
        """
        Opens map and collects raw data
        """
        first_line_nb_drones = False
        payload = {
            'nb_drones': None,
            'hub': [],
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

                elif key == 'start_hub' or key == 'end_hub':
                    payload['hub'].append(cls.FACTORY[key].parse(line))

                else:
                    payload[key].append(cls.FACTORY[key].parse(line))
        
        return cls(**payload)
    
                
    @model_validator(mode='after')
    def validator(self) -> 'Network':
        """
        """
        n_start = [hub for hub in self.hub if hub.type == 'start_hub']
        if not len(n_start) == 1:
            raise ValueError(ERROR['parser']['missing_start_hub'])
        
        n_end = [hub for hub in self.hub if hub.type == 'end_hub']
        if not len(n_end) == 1:
            raise ValueError(ERROR['parser']['missing_end_hub'])
        
        unique_names = {hub.name for hub in self.hub}
        if len(self.hub) > len(unique_names):
            raise ValueError(ERROR['parser']['duplicate_hub_names'])
        
        unique_coords = {hub.coords for hub in self.hub}
        if len(self.hub) > len(unique_coords):
            raise ValueError(ERROR['parser']['duplicate_hub_coords'])
        
        unique_connections = set()
        for connection in self.connection:
            current_connection = tuple(sorted(connection.link))
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
            data += f" [max_link_capacity={c.max_link_capacity}]\n" if c.max_link_capacity else "\n"
        
        return data
