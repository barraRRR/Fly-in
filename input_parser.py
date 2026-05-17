from pydantic import BaseModel, Field, ValidationError, model_validator
from typing import Dict, Any, List, Tuple, Literal, Optional, Protocol
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
    type: Literal['start', 'stop', 'end']
    name: str = Field(pattern=r"^[^- ]*$")
    coords: Tuple[int, int] = Field(default_factory=tuple)
    color: Optional[str] = Field(default=None, pattern=r"^[^ ]*$")
    max_drones: Optional[int] = Field(default=None, ge=1)
    zone: Optional[Zone] = Zone.NORMAL

    @classmethod
    def parse(cls, data: str) -> 'Hub':
        """
        """
        data = data.lower().split(' ')
        type = 'stop' if data[0] not in ['start', 'end'] else data[0]
        name = data[0]

        x = int(data[1])
        y = int(data[2])

        payload = {
            'type': type,
            'name': name,
            'coords': (x, y),
        }

        if data[3]:
            for chunk in data[3:]:
                if '=' not in chunk:
                    raise ValidationError
                meta, value = chunk.split('=')
                meta = meta.strip('[]')
                value = value.strip('[]')
                if meta in ['color', 'max_drones', 'zone']:
                    if meta == 'max_drones':
                        payload[meta] = int(value)
                    else:
                        payload[meta] = value
                else:
                    raise ValidationError(ERROR['metadata'].format(meta=meta))
        
        return cls(**payload)
            

class Connection(BaseModel):
    """
    Parses connection information from raw data
    """
    point_a: str = Field(pattern=r"^[^-]$")
    point_b: str = Field(pattern=r"^[^-]$")
    link: Tuple[str, str] = Field(default_factory=tuple)
    max_link_capacity: int = Field(ge=1)

    @classmethod
    def parse(cls, data: str) -> 'Connection':
        """
        """
        data = data.strip().split(' ')
        if '-' not in data[0]:
            raise ValidationError
        
        point_a, point_b = data[0].split('-')
        payload = {
            'point_a': point_a,
            'point_b': point_b,
            'link': (point_a, point_b)
        }

        if data[1]:
            if '=' not in data[1]:
                raise ValidationError
            
            max_link_capacity = int(data[1].strip('[]').split('=')[1])
            payload['max_link_capacity'] = max_link_capacity
        
        return cls(**payload)


class Network(BaseModel):
    """
    ...
    """
    FACTORY: Dict[str, type[Parser]] = {
        'start_hub': Hub,
        'hub': Hub,
        'end_hub': Hub,
        'connection': Connection
    }
    
    nb_drones: int = Field(ge=1)
    hub: List[Hub] = Field(default_factory=list, min_length=2)
    connection: List[Connection] = Field(default_factory=list)

    @classmethod
    def parser(cls, map: str) -> 'Network':
        """
        Opens map and collects raw data
        """
        first_line_nb_drones = False
        payload = {
            'nb_drones': None,
            'hub': [],
            'connection': []
        }
        try:
            with open(map, 'r') as raw:
                print(STATUS['loading_map'])
                for line in raw:
                    if not line or line.startswith('#'):
                        continue

                    key, data = line.strip().lower().split(':', 1)
                    if not first_line_nb_drones and key != 'nb_drones':
                        raise ValidationError(ERROR['nb_drones_first_item'])
                    
                    elif first_line_nb_drones and key == 'nb_drones':
                        raise ValidationError(ERROR['nb_drones_repeated'])
                    
                    elif key == 'nb_drones':
                        payload['nb_drones'] = int(data)
                        first_line_nb_drones = True

                    elif key == 'start_hub' or key == 'end_hub':
                        payload['hub'].append(cls.FACTORY['hub'].parse(data))

                    else:
                        payload[key].append(cls.FACTORY[key].parse(data))

            return cls(**payload)
        
        except Exception as e:
            sys.exit('tmp')
                
    @model_validator(mode='after')
    def validator(self) -> 'Network':
        """
        """
        n_start = [hub for hub in self.hubs if hub.type == 'start_hub']
        if not 0 < n_start <= 1:
            raise ValidationError
        
        n_end = [hub for hub in self.hubs if hub.type == 'end_hub']
        if not 0 < n_end <= 1:
            raise ValidationError
        
        unique_names = {hub.name for hub in self.hub.name}
        if len(self.hub) > unique_names:
            raise ValidationError
        
        unique_coords = {hub.coords for hub in self.hub.coords}
        if len(self.hub) > unique_coords:
            raise ValidationError
        
        for connection in self.connection:
            unique_connections = {}
            current_connection = set(sorted(connection.link))
            if current_connection in unique_connections:
                raise ValidationError
            unique_connections.add(current_connection)

            if connection.point_a == connection.point_b:
                raise ValidationError
            
            elif connection.point_a not in unique_names:
                raise ValidationError
            
            elif connection.point_b not in unique_names:
                raise ValidationError

        return self
