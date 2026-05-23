from utils import STATUS, ERROR
from typing import Dict, List
import json


class MapParser:
    """
    """
    def __init__(self, path: str) -> None:
        self.path = path
        self.data = self._parse_map()

    def _parse_map(self) -> Dict:
        """
        """
        first_line_nb_drones = False
        payload: Dict = {
            'map': self.path.split("/")[-1].removesuffix(".txt"),
            'nb_drones': None,
            'start_hub': None,
            'hub': [],
            'end_hub': None,
            'connections': []
        }

        with open(self.path, 'r') as f:
            print(STATUS['parsing_map'].format(map=self.path), end='')
            raw = f.readlines()
        print(' OK')
        
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
                payload['start_hub'] = self._parse_hub(line)
                for i in range(payload['nb_drones']):
                    payload['start_hub']['drone_bay'].append(
                        {"id": f"D_{(i + 1):03d}", "status": "standby"}
                    )

            elif key == 'end_hub' and not payload['end_hub']:
                payload['end_hub'] = self._parse_hub(line)

            elif key == 'hub':
                payload['hub'].append(self._parse_hub(line))

            elif key == 'connection':
                payload['connections'].append(self._parse_connection(line))

            else:
                raise ValueError
        
        return payload
    
    @staticmethod
    def _parse_hub(line: str) -> Dict:
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
            'drone_bay': []
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
        
        return payload

    @staticmethod
    def _parse_connection(line: str) -> Dict:
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

        return payload
