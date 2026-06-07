from pathlib import Path
from class_network import Network
from utils import UX
import json


def import_hub_data() -> None:
    """Parses maps to extract and store valid parameters in JSON."""

    hub_data = Path('hub_data.json')
    if hub_data:
        with open('hub_data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            valid_names = set(data['valid_names'])
            invalid_names = data['invalid_names']
            valid_coords = {tuple(coords) for coords in data['valid_coords']}
            invalid_coords = data['invalid_coords']
            valid_colors = set(data['valid_colors'])
            invalid_colors = data['invalid_colors']
    else:
        valid_names = set()
        valid_colors = set()
        valid_coords = set()
    path = Path('maps')

    print(UX["hub_data_found"].format(path=path))
    for file in path.rglob('*.txt'):
        net = Network.parser(file)
        valid_names.update({hub.name for hub in net.hub})
        valid_coords.update({hub.coords for hub in net.hub})
        valid_colors.update({hub.color for hub in net.hub if hub.color})

    payload = {
        'valid_names': sorted(list(valid_names)),
        'invalid_names': sorted(invalid_names),
        'valid_coords': list(valid_coords),
        'invalid_coords': invalid_coords,
        'valid_colors': sorted(list(valid_colors)),
        'invalid_colors': sorted(invalid_colors)
    }

    with open('hub_data.json', 'w', encoding='utf-8') as j:
        json.dump(payload, j, indent=4, ensure_ascii=False)

    print(UX["hub_data_saved"])


if __name__ == '__main__':
    import_hub_data()
