from class_network import Network, Hub, HubType
from typing import List, Dict, Tuple
from blessed import Terminal
from utils import drone_helices


class Gui:
    """
    """
    HUB_WIDTH = 20
    HUB_HEIGHT = 6
    METADATA_HEIGHT = 3
    MARGIN = 2
    
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
        height = (max_y - min_y + 1) * (self.HUB_HEIGHT + self.METADATA_HEIGHT) + self.MARGIN * 2
        
        self.col, self.row = width, height
        self.grid: List[List[Dict[str, str | None]]] = [[{"char": " ", "color": None} for _ in range(self.col)] for _ in range(self.row)]
        self.hub_pos_map: Dict[Hub, Tuple[int,int]] = {}
        self._map_contour()
        self._place_hubs()
        self._place_links()
    
    def update(self, frame: int = 0) -> None:
        """
        """
        self.grid: List[List[Dict[str, str | None]]] = [[{"char": " ", "color": None} for _ in range(self.col)] for _ in range(self.row)]
        self.hub_pos_map: Dict[Hub, Tuple[int,int]] = {}
        self._map_contour()
        self._place_hubs(frame)
        self._place_links(frame)
    
    def _map_contour(self) -> None:
        """
        """
        topbot, sides, top_l = "─", "│", "┌"
        top_r, bot_l, bot_r = "┐", "└", "┘"
        cont_color = "white"

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
        
    def _hub_metadata(self, hub: Hub) -> List[str]:
        """
        """
        occupied = "●" * len(hub.drone_bay)
        available_space = "○" * (hub.max_drones - len(hub.drone_bay))
        bay = f"[{occupied}{available_space}]"
        zone = f"[{hub.zone.name.upper()}]"

        meta_lines = [
            hub.name.center(self.HUB_WIDTH),
            zone.center(self.HUB_WIDTH) if hub.hub_type == HubType.HUB else "",
            bay.center(self.HUB_WIDTH) if hub.hub_type == HubType.HUB else ""
        ]
        
        return meta_lines
    
    def _place_hubs(self, frame: int = 0) -> None:
        """
        """
        hub_lines = [
            "  __  ".center(self.HUB_WIDTH),
            ' |""| '.center(self.HUB_WIDTH),
            "''''''".center(self.HUB_WIDTH)
        ]

        for hub in self.all_hubs:
            x, y = hub.coords
            grid_x = (x - self.min_x) * self.HUB_WIDTH + self.MARGIN
            grid_y = (y - self.min_y) * (self.HUB_HEIGHT + self.METADATA_HEIGHT) + self.MARGIN

            self.hub_pos_map[hub] = (grid_x, grid_y)
            
            """
            if len(hub.drone_bay) > 0:
                drone_x = grid_x + (self.HUB_WIDTH // 2) - 1
                self._place_drone(drone_x, grid_y - 1, frame)
            """
            for i, line in enumerate(hub_lines):
                row = grid_y + i
                if row < self.row - 1:
                    for j, char in enumerate(line):
                        col = grid_x + j
                        if col < self.col - 1:
                            self.grid[row][col]["char"] = char
                            self.grid[row][col]["color"] = hub.color
            
            meta_lines = self._hub_metadata(hub)
            for i, line in enumerate(meta_lines):
                row = grid_y + 3 + i
                if row < self.row - 1:
                    for j, char in enumerate(line):
                        col = grid_x + j
                        if col < self.col - 1:
                            self.grid[row][col]["char"] = char
                            self.grid[row][col]["color"] = None


    def _place_links(self, frame = 0) -> None:
        """
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
                    if link['target_hub'] == dest:
                        max_connections = link['max']
                        incoming = sum([link['incoming_drones'], link['leaving_drones']])
                        info = f"{incoming}/{max_connections}"

                self._draw_smart_line(hub, dest, info, frame)
    
    def _draw_smart_line(
            self,
            hub_a: Hub,
            hub_b: Hub,
            info: str,
            frame: int = 0) -> None:
        """
        """
        self.corners = ["─", "┌", "┐", "└", "┘", "●"]
        self.hor_line = "─"
        self.ver_line = "│"
        self.point = "●"
        self.cross = "┼"

        grid_x1, grid_y1 = self.hub_pos_map[hub_a]
        grid_x2, grid_y2 = self.hub_pos_map[hub_b]
        
        hub_height_center = 2
        
        if grid_x1 < grid_x2:
            x1 = grid_x1 + 14
            x2 = grid_x2 + 5
        elif grid_x1 > grid_x2:
            x1 = grid_x1 + 5
            x2 = grid_x2 + 14
        else:
            x1 = grid_x1 + 14
            x2 = grid_x2 + 14

        y1 = grid_y1 + hub_height_center
        y2 = grid_y2 + hub_height_center

        # traffic
        while self.grid[y1][x1]["char"] == "●":
            y1 -= 1
        while self.grid[y2][x2]["char"] == "●":
            y2 -= 1

        self.grid[y1][x1]["char"], self.grid[y2][x2]["char"] = "●", "●"

        (x1, y1), (x2, y2) = sorted([(x1, y1), (x2, y2)])
        
        self._draw_z_line(x1, y1, x2, y2, info, frame)

    def _draw_line(
            self,
            x1: int, y1: int,
            x2: int, y2: int,
            dir_hor: bool,
            char1: str = "●",
            char2: str = "●",
            info: str = None,
            frame: int = 0) -> Tuple[int, int, int, int]:
        """ 
        Draws a line (horizontal or vertical) on the grid.
        """
        if dir_hor:
            start, end = min(x1, x2), max(x1, x2)
            static_coord = y1
            line_char = "─"
            cross_char = "┼"
        else:
            start, end = min(y1, y2), max(y1, y2)
            static_coord = x1
            line_char = "│"
            cross_char = "┼"

        for i in range(start, end + 1):
            if dir_hor:
                x, y = i, static_coord
            else:
                x, y = static_coord, i

            if not (1 < x < self.col - 1 and 1 < y < self.row - 1):
                continue

            current_char = self.grid[y][x]["char"]
            
            if current_char == line_char:
                self.grid[y][x]["char"] = cross_char
                self.grid[y][x]["color"] = None
            elif current_char != " ":
                continue

            if (dir_hor and i == x1) or (not dir_hor and i == y1):
                self.grid[y][x]["char"] = char1
                self.grid[y][x]["color"] = None
            elif (dir_hor and i == x2) or (not dir_hor and i == y2):
                self.grid[y][x]["char"] = char2
                self.grid[y][x]["color"] = None
            else:
                self.grid[y][x]["char"] = line_char
                self.grid[y][x]["color"] = None

        if info is not None:
            midway_x = (x1 + x2) // 2
            midway_y = (y1 + y2) // 2
            self._place_link_info(midway_x, midway_y, info, frame)
        
        return (x1, y1, x2, y2)
    
    def _draw_z_line(
            self, x1: int, y1: int, x2: int, y2: int, info: str, frame: int = 0) -> None:
        """
        Draws a Z-shaped line (two segments, one horizontal and one vertical, or vice-versa).
        """
        up_right = ["┘", "┌"]
        down_right = ["┐", "└"]
        
        if y2 < y1:
            dir_chars = up_right
        else:
            dir_chars = down_right

        abs_dx = abs(x2 - x1)
        abs_dy = abs(y2 - y1)

        if abs_dx >= abs_dy:
            corner_x, corner_y = x2, y1
  
            self._draw_line(x1, y1, corner_x, corner_y, True, "─", dir_chars[0], info, frame)
            self._draw_line(corner_x, corner_y, x2, y2, False, dir_chars[0], dir_chars[1])
        else:
            corner_x, corner_y = x1, y2
            self._draw_line(x1, y1, corner_x, corner_y, False, "│", dir_chars[0], info, frame)
            self._draw_line(corner_x, corner_y, x2, y2, True, dir_chars[0], dir_chars[1])
    
    def _place_drone(self, x: int, y: int, frame: int = 0) -> str:
        """
        """
        drone1 = "+♦+"
        drone2 = "✕♦✕"
        
        selected = drone1 if frame % 2 == 0 else drone2

        for c in range(len(selected)):
            self.grid[y][x + c]["char"] = selected[c]
            self.grid[y][x + c]["color"] = None

    def _place_link_info(
            self, x: int, y: int, info: str, frame: int = 0) -> None:
        """
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
                place_ok = False if self.grid[off][x - 1]["char"].isdigit() else True
                if place_ok:
                    self._place_drone(x - 1, off, frame)
                    break
                off -= 1

            

    def print_map(self) -> None:
        """
        """
        term = Terminal()
        for row in self.grid:
            for c in row:
                try:
                    color_code = getattr(term, c["color"].lower(), term.normal)
                    print(f"{color_code}{c["char"]}{term.normal}", end="")
        
                except Exception as e:
                    print(c["char"], end="")
            print()
