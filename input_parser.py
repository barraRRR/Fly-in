from pydantic import BaseModel, Field
from typing import Dict, Any, Tuple
from utils import UX, STATUS, ERROR


class ParserError(Exception):
    pass


class Network(BaseModel):
    ...


def parser(map: str) -> Dict[str, Any]:
    """
    Opens map and collects raw data
    """
    network: Dict[str, Any] = {
            'nb_drones': None,
            'hub': [],
            'connections': []            
        }
        
    try:
        with open('map', 'r') as raw:
            print(STATUS['loading_map'])
            for line in raw:
                if not line or line.startswith('#'):
                    continue
                key, data = line.split(':')
                if not network['nb_drones'] and (
                    key.stip().lower() != 'nb_drones'
                    ):
                    raise ParserError(ERROR['nb_drones_first_item'])

                elif key.strip().lower() == 'nb_drones':
                    network['nb_drones'] = data.strip
                
                elif key.strip().lower() in ['start_hub', 'hub', 'end_hub']:
                    data = data.lower().split(' ')
                    name = data[0]
                    x = data[1]
                    y = data[2]
                    network['hub'].append(
                        {
                            'name': name,
                            'x': x,
                            'y': y
                        }
                    )
                    for chunk in data[2:]:
                        meta, value = chunk.split('=')
                        meta = meta.removeprefix('[').removesuffix(']')
                        if meta not in ['color', 'max_drones', 'zone']:
                            raise ParserError(
                                ERROR['metadata'].format(meta=meta)
                                )
                        
                        value = value.removeprefix('[').removesuffix(']')
                        network['hub'][-1][meta] = value

                elif key.strip().lower() == 'connection':
                    data = data.lower().split(' ')
                    if data.count('-') > 1:
                        raise ValueError(ERROR['hyphen'])
                    
                    point_a, point_b = data[0].split('-')
                    network['connections'].append(
                        {
                            'point_a': point_a,
                            'point_b': point_b,
                        }
                    )
                    if len(data) > 1:
                        meta, value = data[1].split('=')
                        if meta != 'max_link_capacity':
                            raise ParserError(
                                ERROR['metadata'].format(meta=meta)
                                )
                        
                        value = value.removeprefix('[').removesuffix(']')
                        network['connections'][-1][meta] = value

                else:
                    raise ParserError(ERROR['invalid_key'].format(key=key))
            
            return network

    except Exception as e:
        print(e)
        return None
