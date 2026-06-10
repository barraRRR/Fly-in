from class_network import Network, Hub, HubType
from typing import List, Dict, Tuple, Set, Any, Optional
import heapq
from blessed import Terminal
import warnings
from utils import UX_MAX, UX_STD, slice_str


class Gui:
    """Manages terminal map representation and dynamic boundaries.

    Args:
        net (Network): The network topology data.
    """

    HUB_WIDTH = 20
    HUB_HEIGHT = 6
    METADATA_HEIGHT = 3
    MARGIN = 2
    PALETTE = {
        "drone_color": "#7B39EB",
        "warning": "#FE7733",
        "pale_green": "#C6FF36",
        "deep_grren": "#243837",
        "line": "#FFFFFF",
    }

    def __init__(self, net: Network) -> None:
        self.net = net
        self.all_hubs = (
            [self.net.start_hub] + self.net.hub + [self.net.end_hub]
        )

        min_x = min(hub.coords[0] for hub in self.all_hubs)
        max_x = max(hub.coords[0] for hub in self.all_hubs)
        min_y = min(hub.coords[1] for hub in self.all_hubs)
        max_y = max(hub.coords[1] for hub in self.all_hubs)

        self.min_x = min_x
        self.min_y = min_y

        width = (max_x - min_x + 1) * self.HUB_WIDTH + self.MARGIN * 2
        height = (max_y - min_y + 1) * (
            self.HUB_HEIGHT + self.METADATA_HEIGHT
        ) + self.MARGIN * 2

        self.col, self.row = width, height
        self.grid: List[List[Dict[str, Optional[str]]]] = [
            [{"char": " ", "color": None} for _ in range(self.col)]
            for _ in range(self.row)
        ]
        self.grid_block: Set[Tuple[int, int]] = set()
        self.hub_pos_map: Dict[Hub, Tuple[int, int]] = {}

        self.corners = ["┌", "┐", "└", "┘"]
        self.hor_line = "─"
        self.ver_line = "│"
        self.point = "■"

        self.term = Terminal()
        self.link_paths_cache: Dict[
            Tuple[str, str], List[Tuple[int, int]]
        ] = {}
        self.color_cache: Dict[str, str] = {}
        self._map_contour()
        self._place_hubs()
        self._place_links()

    def update(self, frame: int = 0) -> None:
        """Updates the graphical grid for the current frame.

        Args:
            frame (int, optional): Animation frame index. Defaults to 0.
        """
        self.grid = [
            [{"char": " ", "color": None} for _ in range(self.col)]
            for _ in range(self.row)
        ]
        self.hub_pos_map = {}
        self.grid_block = set()
        self._map_contour()
        self._place_hubs(frame)
        self._place_links(frame)

    def _map_contour(self) -> None:
        """Generates graphical borders for the UI grid."""
        topbot, sides, top_l = "─", "│", "┌"
        top_r, bot_l, bot_r = "┐", "└", "┘"
        cont_color = self.PALETTE["line"]

        for y in range(self.row):
            for x in range(self.col):
                if y == 0 and x == 0:
                    self.grid[y][x]["char"] = top_l
                    self.grid[y][x]["color"] = cont_color
                elif y == 0 and x == (self.col - 1):
                    self.grid[y][x]["char"] = top_r
                    self.grid[y][x]["color"] = cont_color
                elif y == (self.row - 1) and x == 0:
                    self.grid[y][x]["char"] = bot_l
                    self.grid[y][x]["color"] = cont_color
                elif y == (self.row - 1) and x == (self.col - 1):
                    self.grid[y][x]["char"] = bot_r
                    self.grid[y][x]["color"] = cont_color
                elif y == 0 or y == (self.row - 1):
                    self.grid[y][x]["char"] = topbot
                    self.grid[y][x]["color"] = cont_color
                elif x == 0 or x == (self.col - 1):
                    self.grid[y][x]["char"] = sides
                    self.grid[y][x]["color"] = cont_color
                else:
                    self.grid[y][x]["char"] = " "
                    self.grid[y][x]["color"] = cont_color

    def _place_hubs(self, frame: int = 0) -> None:
        """Draws hub representations on the active grid.

        Args:
            frame (int, optional): Animation frame index. Defaults to 0.
        """
        hub_lines = [
            "  __  ".center(self.HUB_WIDTH),
            ' |""| '.center(self.HUB_WIDTH),
            "''''''".center(self.HUB_WIDTH),
        ]

        for hub in self.all_hubs:
            x, y = hub.coords
            grid_x = (x - self.min_x) * self.HUB_WIDTH + self.MARGIN
            grid_y = (y - self.min_y) * (
                self.HUB_HEIGHT + self.METADATA_HEIGHT
            ) + self.MARGIN

            self.hub_pos_map[hub] = (grid_x, grid_y)

            for i, line in enumerate(hub_lines):
                row = grid_y + i
                if row < self.row - 1:
                    for j, char in enumerate(line):
                        col = grid_x + j
                        if col < self.col - 1:
                            self.grid[row][col]["char"] = char
                            self.grid[row][col]["color"] = hub.color
                            if not char.isspace():
                                self.grid_block.add((col, row))

            len_bay = len(hub.drone_bay)
            occupied = "●" * len_bay
            available_space = "○" * (hub.max_drones - len_bay)
            bay = f"[{occupied}{available_space}]"
            zone = f"[{hub.zone.name.upper()}]"

            if hub.hub_type == HubType.HUB:
                meta_lines = [
                    hub.name.center(self.HUB_WIDTH),
                    zone.center(self.HUB_WIDTH),
                    bay.center(self.HUB_WIDTH),
                ]
            else:
                drone_lines = (
                    [
                        f"[{occupied[i: i + 5]}]"
                        for i in range(0, max(1, len_bay), 5)
                    ]
                    if len_bay
                    else []
                )
                meta_lines = [hub.name.center(self.HUB_WIDTH)] + [
                    line.center(self.HUB_WIDTH) for line in drone_lines
                ]

            for i, line in enumerate(meta_lines):
                row = grid_y + 3 + i
                if "○" in line or "●" in line:
                    color_code = self.PALETTE["drone_color"]
                else:
                    color_code = None

                if row < self.row - 1:
                    for j, char in enumerate(line):
                        col = grid_x + j
                        if col < self.col - 1:
                            self.grid[row][col]["char"] = char
                            self.grid[row][col]["color"] = color_code
                            if not char.isspace():
                                self.grid_block.add((col, row))

    def _place_links(self, frame: int = 0) -> None:
        """Draws the connecting lines between hubs using A* routing.

        Args:
            frame (int, optional): Animation frame index. Defaults to 0.
        """
        established_links = []
        sorted_hubs = sorted(
            self.all_hubs, key=lambda h: h.coords[1], reverse=True
        )
        for hub in sorted_hubs:
            all_dest = [link["target_hub"] for link in hub.links]
            all_dest.sort(key=lambda p: p.coords[1])

            while all_dest:
                dest = all_dest.pop()
                pair = tuple(sorted([hub.name, dest.name]))
                if pair in established_links:
                    continue
                established_links.append(pair)

                for link in hub.links:
                    if link["target_hub"] == dest:
                        max_connections = link["max"]
                        incoming = sum(
                            [link["incoming_drones"], link["leaving_drones"]]
                        )
                        info = f"{incoming}/{max_connections}"

                grid_x1, grid_y1 = self.hub_pos_map[hub]
                grid_x2, grid_y2 = self.hub_pos_map[dest]

                hub_height_center = 2
                y1 = grid_y1 + hub_height_center
                y2 = grid_y2 + hub_height_center

                if grid_x1 < grid_x2:
                    x1 = grid_x1 + 14
                    x2 = grid_x2 + 5
                elif grid_x1 > grid_x2:
                    x1 = grid_x1 + 5
                    x2 = grid_x2 + 14
                else:
                    x1 = grid_x1 + 14
                    x2 = grid_x2 + 14

                while self.grid[y1][x1]["char"] == "■":
                    y1 -= 1
                while self.grid[y2][x2]["char"] == "■":
                    y2 -= 1

                self.grid[y1][x1]["char"] = "■"
                self.grid[y2][x2]["char"] = "■"

                if pair not in self.link_paths_cache:
                    line = self._find_line(x1, y1, x2, y2)
                    self.link_paths_cache[pair] = line
                else:
                    line = self.link_paths_cache[pair]

                self._fill_line(line, info, frame)
                self.grid_block.add((x1, y1))
                self.grid_block.add((x2, y2))

    def _find_line(
        self, x1: int, y1: int, x2: int, y2: int
    ) -> List[Tuple[int, int]]:
        """Finds an obstacle-free path using the A* search algorithm.

        Args:
            x1 (int): Starting X coordinate.
            y1 (int): Starting Y coordinate.
            x2 (int): Destination X coordinate.
            y2 (int): Destination Y coordinate.

        Returns:
            List[Tuple[int, int]]: Sequential coordinates of the path.
        """
        tie_breaker = 0
        # Queue: (f_score, turns, order, cx, cy, dir_x, dir_y, path)
        queue = [(0, 0, tie_breaker, x1, y1, 0, 0, [(x1, y1)])]
        best_costs: Dict[Tuple[int, int, int, int], Tuple[int, int]] = {}

        while queue:
            f_score, turns, _, cx, cy, c_dx, c_dy, path = heapq.heappop(queue)

            if (cx, cy) == (x2, y2):
                return path

            abs_dx = abs(x2 - cx)
            abs_dy = abs(y2 - cy)
            target_dx = 1 if x2 > cx else (-1 if x2 < cx else 0)
            target_dy = 1 if y2 > cy else (-1 if y2 < cy else 0)

            moves = []
            if abs_dx >= abs_dy:
                if target_dx != 0:
                    moves.append((cx + target_dx, cy))
                if target_dy != 0:
                    moves.append((cx, cy + target_dy))
                if target_dy == 0:
                    moves.extend([(cx, cy + 1), (cx, cy - 1)])
                if target_dx != 0:
                    moves.append((cx - target_dx, cy))
                if target_dy != 0:
                    moves.append((cx, cy - target_dy))
            else:
                if target_dy != 0:
                    moves.append((cx, cy + target_dy))
                if target_dx != 0:
                    moves.append((cx + target_dx, cy))
                if target_dx == 0:
                    moves.extend([(cx + 1, cy), (cx - 1, cy)])
                if target_dy != 0:
                    moves.append((cx, cy - target_dy))
                if target_dx != 0:
                    moves.append((cx - target_dx, cy))

            unique_moves = []
            for m in moves:
                if m not in unique_moves:
                    unique_moves.append(m)

            for nx, ny in unique_moves:
                if (nx, ny) not in self.grid_block:
                    if 0 <= nx < self.col and 0 <= ny < self.row:
                        n_dx = nx - cx
                        n_dy = ny - cy
                        is_valid = True

                        current_char = self.grid[cy][cx]["char"]
                        if current_char == "│" and nx == cx:
                            is_valid = False
                        elif current_char == "─" and ny == cy:
                            is_valid = False

                        if is_valid and (nx, ny) != (x2, y2):
                            target_char = self.grid[ny][nx]["char"]
                            if nx != cx and target_char not in [" ", "│"]:
                                is_valid = False
                            elif nx == cx and target_char not in [" ", "─"]:
                                is_valid = False

                        if is_valid:
                            new_len = len(path)
                            is_turn = (
                                1
                                if (
                                    (c_dx, c_dy) != (0, 0)
                                    and (c_dx, c_dy) != (n_dx, n_dy)
                                )
                                else 0
                            )
                            new_turns = turns + is_turn

                            state_key = (nx, ny, n_dx, n_dy)

                            if state_key not in best_costs or best_costs[
                                state_key
                            ] > (new_len, new_turns):
                                best_costs[state_key] = (new_len, new_turns)

                                h = abs(x2 - nx) + abs(y2 - ny)
                                f = new_len + h
                                tie_breaker += 1

                                heapq.heappush(
                                    queue,
                                    (
                                        f,
                                        new_turns,
                                        tie_breaker,
                                        nx,
                                        ny,
                                        n_dx,
                                        n_dy,
                                        path + [(nx, ny)],
                                    ),
                                )

        return []

    def _fill_line(
        self, line: List[Tuple[int, int]], info: Optional[str], frame: int = 0
    ) -> None:
        """Draws the path trajectory characters on the grid.

        Args:
            line (List[Tuple[int, int]]): Path coordinates.
            info (str, optional): Traffic capacity text. Defaults to None.
            frame (int, optional): Animation frame index. Defaults to 0.
        """
        for i in range(1, len(line) - 1):
            px, py = line[i - 1]
            dx, dy = line[i]
            nx, ny = line[i + 1]

            left = (px < dx) or (nx < dx)
            right = (px > dx) or (nx > dx)
            up = (py < dy) or (ny < dy)
            down = (py > dy) or (ny > dy)

            if left and right:
                char = "─"
            elif up and down:
                char = "│"
            elif left and up:
                char = "┘"
            elif left and down:
                char = "┐"
            elif right and up:
                char = "└"
            elif right and down:
                char = "┌"
            else:
                continue

            if self.grid[dy][dx]["char"] == " ":
                self.grid[dy][dx]["char"] = char
                self.grid[dy][dx]["color"] = self.PALETTE["line"]

            if i == len(line) // 2:
                self._place_link_info(dx, dy, str(info), frame)

    def _place_drone(self, x: int, y: int, frame: int = 0) -> None:
        """Places drone ASCII representation on the grid.

        Args:
            x (int): Horizontal coordinate.
            y (int): Vertical coordinate.
            frame (int, optional): Animation frame index. Defaults to 0.
        """
        drone1 = "+♦+"
        drone2 = "✕♦✕"

        selected = drone1 if frame % 2 == 0 else drone2

        for c in range(len(selected)):
            self.grid[y][x + c]["char"] = selected[c]
            self.grid[y][x + c]["color"] = self.PALETTE["drone_color"]

    def _place_link_info(
        self, x: int, y: int, info: str, frame: int = 0
    ) -> None:
        """Anchors traffic capacity metrics text on the route.

        Args:
            x (int): X coordinate for text.
            y (int): Y coordinate for text.
            info (str): The traffic data string.
            frame (int, optional): Animation frame index. Defaults to 0.
        """
        mid = len(info) // 2
        for i, char in enumerate(info):
            x_pos = x + i - mid
            if 0 <= x_pos <= self.col and 0 <= y <= self.row:
                self.grid[y][x + i - mid]["char"] = char
                self.grid[y][x + i - mid]["color"] = None

        if not info.startswith("0"):
            off = y - 1
            iterations = 0
            while iterations <= 5:
                iterations += 1
                char_at_pos = self.grid[off][x - 1]["char"]
                place_ok = char_at_pos is None or not char_at_pos.isdigit()

                if place_ok:
                    self._place_drone(x - 1, off, frame)
                    break
                off -= 1

    def _get_colored_char(self, c: Optional[str], color: Optional[str]) -> str:
        """Applies terminal color codes to a given character.

        Args:
            c (str): The character to format.
            color (str | None): Color name or hex code.

        Returns:
            str: Formatted string with color codes.
        """
        if c is None:
            c = " "
        if not color or color == "rainbow":
            return c

        if color not in self.color_cache:
            try:
                if color.startswith("#"):
                    self.color_cache[color] = self.term.color_hex(color)
                else:
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore", UserWarning)
                        self.color_cache[color] = getattr(
                            self.term, color.lower(), self.term.normal
                        )
            except Exception:
                self.color_cache[color] = ""

        color_code = self.color_cache[color]
        if color_code:
            return f"{color_code}{c}{self.term.normal}"
        return c

    def print_grid(self, grid: List[List[Dict[str, Optional[str]]]]) -> None:
        """Renders the entire UI grid to the terminal.

        Args:
            grid (List[List[Dict[str, str]]]): The layout matrix to print.
        """
        for row in grid:
            print(
                "".join(
                    self._get_colored_char(c["char"], c["color"]) for c in row
                )
            )

    def _place_map_name(self, map_name: str) -> None:
        """Prints the formatted map title banner.

        Args:
            map_name (str): The name of the map.
        """
        col = self.col if self.col < UX_MAX else UX_STD
        print(
            "┌"
            + "─" * (col - 2)
            + "┐\n"
            + "│"
            + map_name.upper().center(col - 2)
            + "│\n"
            "└" + "─" * (col - 2) + "┘"
        )

    def _text_pannel(
        self,
        drones_left: int,
        turn_num: int,
        col_left: List[str],
        col_right: List[str],
        map_name: str,
        text_margin: int = 6,
    ) -> None:
        """Renders information panels with simulation status and logs.

        Args:
            drones_left (int): Remaining drones count.
            turn_num (int): Current turn index.
            col_left (List[str]): Drone status event logs.
            col_right (List[str]): Turn completion logs.
            map_name (str): Name of the current map.
            text_margin (int, optional): Center margin width. Defaults to 6.
        """
        col = self.col if self.col < UX_MAX else UX_STD
        sub_size = col // 2 - (text_margin // 2)
        title = " STATUS ".center(col, "=")
        info_drones = f"Drones left: {drones_left:03d}".center(col)
        info_turns = f"Total turns: {turn_num:03d}".center(col)
        bottom = "".center(col, "=")

        def _place_subtitle(
            sub1: str, sub2: str, size: int, margin: int
        ) -> str:
            return (
                "┌"
                + "─" * (size - 2)
                + "┐"
                + " " * margin
                + "┌"
                + "─" * (size - 2)
                + "┐\n"
                + "│"
                + sub1.center(size - 2)
                + "│"
                + " " * margin
                + "│"
                + sub2.center(size - 2)
                + "│\n"
                + "└"
                + "─" * (size - 2)
                + "┘"
                + " " * margin
                + "└"
                + "─" * (size - 2)
                + "┘\n"
            )

        subtitles = _place_subtitle(
            "DRONE LOG", "TURN LOG", sub_size, text_margin
        )

        print("\n".join([title, info_drones, info_turns, bottom, subtitles]))

        max_lines = 10
        row = max_lines
        max_char_line = col // 2 - (text_margin // 2)

        col_left = slice_str(col_left, max_char_line, max_lines)
        col_right = slice_str(col_right, max_char_line, max_lines)

        grid: List[List[Dict[str, Optional[str]]]] = [
            [{"char": " ", "color": self.PALETTE["line"]} for _ in range(col)]
            for _ in range(row)
        ]

        for y, line in enumerate(col_left):
            if y >= row:
                break

            if "[SUCCESS]" in line:
                color_code = self.PALETTE["pale_green"]
            elif "[TURN" in line:
                color_code = self.PALETTE["drone_color"]
            elif "[WARNING]" in line:
                color_code = self.PALETTE["warning"]
            else:
                color_code = self.PALETTE["line"]

            for x, char in enumerate(line):
                if x >= max_char_line:
                    break
                grid[y][x]["char"] = char
                grid[y][x]["color"] = color_code

        off = max_char_line + text_margin

        for y, line in enumerate(col_right):
            if y >= row:
                break
            for x, char in enumerate(line):
                if x >= max_char_line:
                    break
                grid[y][x + off]["char"] = char

        self.print_grid(grid)

    def _metrics_panel(self, metrics: Dict[str, Any]) -> None:
        """Displays the final performance metrics summary.

        Args:
            metrics (Dict[str, Any]): Evaluation payload.
        """
        col = self.col if self.col < UX_MAX else UX_STD

        min_turns = metrics["min_turns"]
        max_turns = metrics["max_turns"]
        drones_per_turn = metrics["drones_moved_per_turn"]
        avg_drone = metrics["avg_turns_per_drone"]
        total_cost = metrics["total_path_cost"]
        total_turns = metrics["current_turn"]

        title = " SUCCESS! ".center(col, "=")
        pannel = (
            f"Total path cost       : {total_cost:03d}    "
            f"Min turns   : {min_turns:03d}".center(
                self.col, " "
            )
            + "\n"
            + f"Drones moved per turn : {int(drones_per_turn):02d}%    "
            f"Max turns   : {max_turns:03d}".center(
                self.col, " "
            )
            + "\n"
            + f"Turns per drone       : {int(avg_drone):03d}    "
            f"Total turns : {total_turns:03d}".center(
                self.col, " "
            )
        )

        bottom = "".center(col, "=")
        print("\n" + "\n".join([title, pannel, bottom]))
