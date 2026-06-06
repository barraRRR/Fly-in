# importar textos ok
# importat textos fail
from class_network import Network
from class_parser import MapParser
from pathlib import Path
from typing import Generator, Tuple, Optional, Union
import pytest
import json
import copy
import tempfile
import random


maps = list(Path('maps').rglob('*.txt'))

with open('hub_data.json', 'r', encoding='utf-8') as f:
    hub_data = json.load(f)


def get_random_data(
        valid_zone: bool = True,
        valid_nb_drones: bool = True,
        valid_name: bool = True,
        valid_coord: bool = True,
        valid_color: bool = True,
        valid_max_drones: bool = True,
) -> Generator[Tuple[int, str, Tuple[int, int], str], Optional[dict], None]:
    """Generates random combinations for mapping data objects to facilitate
    diverse map testing boundaries.

    Args:
        valid_zone (bool): Generate a syntactically correct node zone
            status. Defaults to True.
        valid_nb_drones (bool): Supply logical positive drone numeric flags.
            Defaults to True.
        valid_name (bool): Map accurate existing string titles. Defaults
            to True.
        valid_coord (bool): Create valid geometric tuple coordinates.
            Defaults to True.
        valid_color (bool): Yield compatible termcolor arguments. Defaults
            to True.
        valid_max_drones (bool): Create realistic max_capacity integer
            values. Defaults to True.

    Yields:
        Tuple[int, str, Tuple[int, int], str]: Emitted object components
            required to stitch mapping rules dynamically.
    """
    data_copy = copy.deepcopy(hub_data)
    random.shuffle(data_copy['valid_names'])
    random.shuffle(data_copy['valid_coords'])
    random.shuffle(data_copy['valid_colors'])
    zones = ["normal", "priority", "restricted", "blocked"]
    while True:
        nb_drones = random.randint(1, 25) if valid_nb_drones else -1
        max_drones = random.randint(1, 5) if valid_max_drones else -1
        zone = random.choice(zones) if valid_zone else "foo"
        if valid_name:
            name = data_copy['valid_names'].pop()
        else:
            name = data_copy['invalid_names'].pop()
        if valid_coord:
            coords = data_copy['valid_coords'].pop()
        else:
            coords = data_copy['invalid_coords'].pop()
        if valid_color:
            color = random.choice(data_copy['valid_colors'])
        else:
            color = random.choice(data_copy['invalid_colors'])

        new_args = yield (nb_drones, name, coords, color, max_drones, zone)

        if new_args is not None:
            if 'valid_name' in new_args:
                valid_name = new_args['valid_name']
            if 'valid_coord' in new_args:
                valid_coord = new_args['valid_coord']
            if 'valid_color' in new_args:
                valid_color = new_args['valid_color']
            if 'valid_zone' in new_args:
                valid_zone = new_args['valid_zone']
            if 'valid_nb_drones' in new_args:
                valid_nb_drones = new_args['valid_nb_drones']
            if 'valid_max_drones' in new_args:
                valid_max_drones = new_args['valid_max_drones']


def get_payload(
        valid_zone: bool = True,
        valid_nb_drones: bool = True,
        valid_name: bool = True,
        valid_coord: bool = True,
        valid_color: bool = True,
        valid_max_drones: bool = True,
        valid_max_link: bool = True
) -> str:
    """Pulls random properties establishing a functional flat textual file
    representation matching project .txt boundaries.

    Args:
        valid_zone (bool): If True ensures properties are valid. Defaults to True.
        valid_nb_drones (bool): If True ensures positive drone numbers. Defaults to True.
        valid_name (bool): Defaults to True.
        valid_coord (bool): Defaults to True.
        valid_color (bool): Defaults to True.
        valid_max_drones (bool): Defaults to True.
        valid_max_link (bool): Defaults to True.

    Returns:
        str: Multi-line string identical to expected `fly_in.py` parser map
            definitions.
    """
    gen_data = get_random_data(
        valid_zone=valid_zone,
        valid_nb_drones=valid_nb_drones,
        valid_name=valid_name,
        valid_coord=valid_coord,
        valid_color=valid_color,
        valid_max_drones=valid_max_drones)
    nb_drones, name, coords, color, max_drones, zone = next(gen_data)
    hubs = [name]
    payload = (
        f"nb_drones: {nb_drones}\n"
        f"start_hub: {name} {coords[0]} {coords[1]} "
        f"[color={color} zone={zone} max_drones={max_drones}]\n"
    )
    for _ in range(random.randint(1, 10)):
        _, name, coords, color, max_drones, zone = next(gen_data)
        hubs.append(name)
        payload += (
            f"hub: {name} {coords[0]} {coords[1]} "
            f"[color={color} zone={zone} max_drones={max_drones}]\n"
        )
    _, name, coords, color, max_drones, zone = next(gen_data)
    hubs.append(name)
    payload += (
        f"end_hub: {name} {coords[0]} {coords[1]} "
        f"[color={color} zone={zone} max_drones={max_drones}]\n"
    )
    links = 0
    unique_links = []
    while links < 3:
        point_a = random.choice(hubs)
        point_b = random.choice(hubs)
        max_link = random.randint(1, 5) if valid_max_link else -1
        current_link = sorted((point_a, point_b))
        if current_link in unique_links:
            continue
        elif point_a == point_b:
            continue
        unique_links.append(current_link)
        payload += (
            f"connection: {point_a}-{point_b} [max_link_capacity={max_link}]\n"
        )
        links += 1

    return payload


class TestNetwork:
    ITERATIONS = 7

    @pytest.mark.parametrize('file_path', maps, ids=lambda p: p.name)
    def test_parser(self, file_path: str) -> None:
        """Iterates explicitly across valid map `.txt` assets asserting
        that syntax parses without error.

        Args:
            file_path (str): Relative string pointing directly against root
                project maps sub-directory.
        """
        map = MapParser(str(file_path))
        net = Network(**map.data)
        print(net.get_map_info())
        assert True

    @pytest.mark.parametrize('_', range(ITERATIONS))
    def test_valid_data(self, _) -> None:
        """Creates volatile random map datasets mimicking standard behavior
        successfully parsing them.

        Args:
            _ (int): Parametrized loop index ignoring argument capture natively.
        """
        payload = get_payload()
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write(payload)
            f.flush()
            temp_file = f.name

        map = MapParser(temp_file)
        net = Network(**map.data)
        assert True

    @pytest.mark.parametrize('_', range(ITERATIONS))
    def test_invalid_name(self, _) -> None:
        """Tests parser boundary triggering validation exceptions against
        improperly constructed name mapping strings.

        Args:
            _ (int): Parametrized range variable iterator implicitly.
        """
        with pytest.raises(ValueError):
            payload = get_payload(valid_name=False)
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
                f.write(payload)
                f.flush()
                temp_file = f.name

            map = MapParser(temp_file)
            net = Network(**map.data)

    @pytest.mark.parametrize('_', range(ITERATIONS))
    def test_invalid_coords(self, _) -> None:
        """Enforces runtime exception bounds identifying structurally errant
        tuple arrays targeting integer layouts randomly constructed.

        Args:
            _ (int): Parametrized iteration flag.
        """
        with pytest.raises(ValueError):
            payload = get_payload(valid_coord=False)
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
                f.write(payload)
                f.flush()
                temp_file = f.name

            map = MapParser(temp_file)
            net = Network(**map.data)

    @pytest.mark.parametrize('_', range(ITERATIONS))
    def test_invalid_color(self, _) -> None:
        """Fails gracefully upon invalid color palette ingestion inside map
        hub configurations dynamically triggered.

        Args:
            _ (int): Parametrized iteration flag.
        """
        with pytest.raises(ValueError):
            payload = get_payload(valid_color=False)
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
                f.write(payload)
                f.flush()
                temp_file = f.name

            map = MapParser(temp_file)
            net = Network(**map.data)

    @pytest.mark.parametrize('_', range(ITERATIONS))
    def test_invalid_zone(self, _) -> None:
        """Provokes deliberate failure against unrecognizable Zone ENUM
        implementations embedded across hub metadata dynamically generated
        strings randomly mapped.

        Args:
            _ (int): Parametrized iteration flag.
        """
        with pytest.raises(ValueError):
            payload = get_payload(valid_zone=False)
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
                f.write(payload)
                f.flush()
                temp_file = f.name

            map = MapParser(temp_file)
            net = Network(**map.data)

    @pytest.mark.parametrize('_', range(ITERATIONS))
    def test_invalid_max_drones(self, _) -> None:
        """Secures exception blocks resolving improperly assigned capacity
        sizes bounding node elements internally instantiated.

        Args:
            _ (int): Parametrized iteration flag.
        """
        with pytest.raises(ValueError):
            payload = get_payload(valid_max_drones=False)
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
                f.write(payload)
                f.flush()
                temp_file = f.name

            map = MapParser(temp_file)
            net = Network(**map.data)

    @pytest.mark.parametrize('_', range(ITERATIONS))
    def test_invalid_max_link(self, _) -> None:
        """Guarantees exceptions capturing improperly constrained connection
        links parsed through the flat mapping documents.

        Args:
            _ (int): Parametrized loop mapping bounds logically executed
                randomly across test frameworks safely.
        """
        with pytest.raises(ValueError):
            payload = get_payload(valid_max_link=False)
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
                f.write(payload)
                f.flush()
                temp_file = f.name

            map = MapParser(temp_file)
            net = Network(**map.data)
