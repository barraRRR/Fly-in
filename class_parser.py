from utils import STATUS, ERROR
from typing import Dict, Any
from utils import UX


class MapParser:
    """Parses map text files into network dictionaries.

    Args:
        path (str): Relative path to the map file.
    """

    def __init__(self, path: str) -> None:
        self.path = path
        self.data = self._parse_map()

    def _parse_map(self) -> Dict[str, Any]:
        """Reads the map file and populates the network data dictionary.

        Returns:
            Dict: Network topology data.

        Raises:
            ValueError: On structural parsing faults or invalid schema.
        """
        first_line_nb_drones = False
        payload: Dict[str, Any] = {
            "map": self.path.split("/")[-1].removesuffix(".txt"),
            "nb_drones": None,
            "start_hub": None,
            "hub": [],
            "end_hub": None,
            "connections": [],
        }

        with open(self.path, "r") as f:
            print(STATUS["parsing_map"].format(map=self.path), end="")
            raw = f.readlines()
        print(UX["ok"])
        for line in raw:
            clean_line = line.strip()
            if not clean_line or clean_line.startswith("#"):
                continue

            key, data = clean_line.lower().split(":", 1)
            key = key.strip()
            data = data.strip()

            if not first_line_nb_drones and key != "nb_drones":
                raise ValueError(ERROR["parser"]["nb_drones_first_item"])

            elif first_line_nb_drones and key == "nb_drones":
                raise ValueError(ERROR["parser"]["nb_drones_repeated"])

            elif key == "nb_drones":
                try:
                    payload["nb_drones"] = int(data)
                except ValueError:
                    raise ValueError(ERROR["parser"]["nb_drones_first_item"])
                first_line_nb_drones = True

            elif key == "start_hub" and not payload["start_hub"]:
                payload["start_hub"] = self._parse_hub(line)
                for i in range(payload["nb_drones"]):
                    payload["start_hub"]["drone_bay"].append(
                        {"id": f"D{(i + 1)}", "status": "standby"}
                    )

            elif key == "end_hub" and not payload["end_hub"]:
                payload["end_hub"] = self._parse_hub(line)

            elif key == "hub":
                payload["hub"].append(self._parse_hub(line))

            elif key == "connection":
                conn = self._parse_connection(line)
                defined_hubs = [h["name"] for h in payload["hub"]]
                if payload["start_hub"]:
                    defined_hubs.append(payload["start_hub"]["name"])
                if payload["end_hub"]:
                    defined_hubs.append(payload["end_hub"]["name"])

                for pt in [conn["point_a"], conn["point_b"]]:
                    if pt not in defined_hubs:
                        raise ValueError(
                            ERROR["parser"]["missing_hub"].format(point=pt)
                            )

                payload["connections"].append(conn)

            else:
                raise ValueError(
                    ERROR["parser"]["invalid_key"].format(key=key)
                    )

        if not payload["start_hub"]:
            raise ValueError(ERROR["parser"]["missing_start_hub"])
        if not payload["end_hub"]:
            raise ValueError(ERROR["parser"]["missing_end_hub"])

        return payload

    @staticmethod
    def _parse_hub(line: str) -> Dict[str, Any]:
        """Extracts hub configuration data from a text line.

        Args:
            line (str): Raw text line matching hub formatting.

        Returns:
            Dict: Hub title, coordinates, and configurations.
        """
        line = line.lower().strip()
        hub_type, data_raw = line.split(":", 1)
        hub_type = hub_type.strip(" :")
        data = data_raw.strip().split(" ")

        if len(data) < 3 or not data[0]:
            raise ValueError(ERROR["parser"]["invalid_hub_format"])

        name = data[0]
        try:
            x = int(data[1])
            y = int(data[2])
        except ValueError:
            raise ValueError(
                ERROR["parser"]["invalid_coordinates"].format(name=name)
                )

        payload: Dict[str, Any] = {
            "hub_type": hub_type,
            "name": name,
            "coords": (x, y),
            "drone_bay": [],
        }

        try:
            flag_max_drones = False
            flag_color = False
            flag_zone = False
            for chunk in data[3:]:
                if "=" not in chunk:
                    raise ValueError(
                        ERROR["parser"]["invalid_metadata_format"]
                        )
                meta, value_raw = chunk.split("=")
                meta = meta.strip("[]")
                value = value_raw.strip("[]")

                if meta == "max_drones":
                    if flag_max_drones:
                        raise ValueError(
                            ERROR["parser"][
                                "invalid_metadata_duplicate"
                                ].format(meta=meta)
                            )
                    try:
                        payload[meta] = int(value)
                    except ValueError:
                        raise ValueError(
                            ERROR["parser"][
                                "invalid_max_drones"
                                ].format(name=name)
                            )

                    flag_max_drones = True

                elif meta == "color":
                    if flag_color:
                        raise ValueError(
                            ERROR["parser"][
                                "invalid_metadata_duplicate"
                                ].format(meta=meta)
                            )
                    payload[meta] = value
                    flag_color = True

                elif meta == "zone":
                    if flag_zone:
                        raise ValueError(
                            ERROR["parser"][
                                "invalid_metadata_duplicate"
                                ].format(meta=meta)
                            )
                    payload[meta] = value
                    flag_zone = True

                else:
                    raise ValueError(
                        ERROR["parser"]["metadata"].format(meta=meta)
                    )

        except IndexError:
            pass

        return payload

    @staticmethod
    def _parse_connection(line: str) -> Dict[str, Any]:
        """Extracts connection data mapping targets and capacities.

        Args:
            line (str): Text row referencing direct connections.

        Returns:
            Dict: Start and end nodes with connection capacity.
        """
        line = line.lower().strip()
        data_raw = line.split(":", 1)[1]
        data = data_raw.strip().split(" ")
        if "-" not in data[0]:
            raise ValueError(ERROR["parser"]["invalid_connection_format"])

        point_a, point_b = data[0].split("-")
        payload: Dict[str, Any] = {
            "point_a": point_a,
            "point_b": point_b,
        }

        if len(data) == 2:

            if "=" not in data[1]:
                raise ValueError(ERROR["parser"]["invalid_capacity_format"])

            max_link_capacity = data[1].strip("[]").split("=")[1]

            try:
                payload["max_link_capacity"] = int(max_link_capacity)

            except ValueError:
                raise ValueError(ERROR["parser"]["invalid_capacity_format"])

        elif len(data) > 2:
            raise ValueError(ERROR["parser"]["invalid_capacity_format"])

        return payload
