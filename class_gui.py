from class_network import Network, Hub, HubType
from typing import List, Dict, Tuple
from colored import fg, attr, style


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
        self.grid: List[List[str]] = [[" " for _ in range(self.col)] for _ in range(self.row)]
        self.hub_pos_map: Dict[Hub, Tuple[int,int]] = {}
        self._map_contour()
        self._place_hubs()
        self._place_links()
    
    def update(self) -> None:
        """
        """
        self.grid: List[List[str]] = [[" " for _ in range(self.col)] for _ in range(self.row)]
        self.hub_pos_map: Dict[Hub, Tuple[int,int]] = {}
        self._map_contour()
        self._place_hubs()
        self._place_links()
    
    def _map_contour(self) -> None:
        """
        """
        topbot, sides, top_l = "─", "│", "┌"
        top_r, bot_l, bot_r = "┐", "└", "┘"

        for y in range(self.row):
            for x in range(self.col):
                if y == 0 and x == 0:
                    self.grid[y][x] = top_l
                elif y == 0 and x == (self.col - 1):
                    self.grid[y][x] = top_r
                elif y == (self.row - 1) and x == 0:
                    self.grid[y][x] = bot_l
                elif y == (self.row - 1) and x == (self.col - 1):
                    self.grid[y][x] = bot_r
                elif y == 0 or y == (self.row - 1):
                    self.grid[y][x] = topbot
                elif x == 0 or x == (self.col - 1):
                    self.grid[y][x] = sides
                else:
                    self.grid[y][x] = " "
        
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
    
    def _place_hubs(self) -> None:
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
            
            for i, line in enumerate(hub_lines):
                row = grid_y + i
                if row < self.row - 1:
                    for j, char in enumerate(line):
                        col = grid_x + j
                        if col < self.col - 1:
                            self.grid[row][col] = char
            
            meta_lines = self._hub_metadata(hub)
            for i, line in enumerate(meta_lines):
                row = grid_y + 3 + i
                if row < self.row - 1:
                    for j, char in enumerate(line):
                        col = grid_x + j
                        if col < self.col - 1:
                            self.grid[row][col] = char

    def _place_links(self) -> None:
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
                        incoming = link['incoming_drones']
                        info = f"{incoming}/{max_connections}"

                self._draw_smart_line(hub, dest, info)
    
    def _draw_smart_line(
            self,
            hub_a: Hub,
            hub_b: Hub,
            info: str) -> None:
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
        while self.grid[y1][x1] == "●":
            y1 -= 1
        while self.grid[y2][x2] == "●":
            y2 -= 1

        self.grid[y1][x1], self.grid[y2][x2] = "●", "●"

        (x1, y1), (x2, y2) = sorted([(x1, y1), (x2, y2)])
        
        self._draw_z_line(x1, y1, x2, y2, info)

    def _draw_line(
            self,
            x1: int, y1: int,
            x2: int, y2: int,
            dir_hor: bool,
            char1: str = "●",
            char2: str = "●",
            info: str = None) -> Tuple[int, int, int, int]:
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

            current_char = self.grid[y][x]
            
            if current_char == line_char:
                self.grid[y][x] = cross_char
            elif current_char != " ":
                continue

            if (dir_hor and i == x1) or (not dir_hor and i == y1):
                self.grid[y][x] = char1
            elif (dir_hor and i == x2) or (not dir_hor and i == y2):
                self.grid[y][x] = char2
            else:
                self.grid[y][x] = line_char

        if info is not None:
            midway_x = (x1 + x2) // 2
            midway_y = (y1 + y2) // 2
            self._place_link_info(midway_x, midway_y, info)
        
        return (x1, y1, x2, y2)
    
    def _draw_z_line(
            self, x1: int, y1: int, x2: int, y2: int, info: str) -> None:
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
  
            self._draw_line(x1, y1, corner_x, corner_y, True, "─", dir_chars[0], info)
            self._draw_line(corner_x, corner_y, x2, y2, False, dir_chars[0], dir_chars[1])
        else:
            corner_x, corner_y = x1, y2
            self._draw_line(x1, y1, corner_x, corner_y, False, "│", dir_chars[0], info)
            self._draw_line(corner_x, corner_y, x2, y2, True, dir_chars[0], dir_chars[1])
    
    def _is_safe(self, x1: int, y1: int, x2: int, y2, dir_char: str) -> bool:
        """
        """
        danger = ["─", "┌", "┐", "└", "┘", "●"]
        if dir_char == "─":
            for x in range(min(x1, x2), max(x1, x2) + 1):
                if self.grid[y1][x] in danger + [dir_char] and (x, y1) != (x2, y2):
                    return False
            return True
        elif dir_char == "│":
            for y in range(min(y1, y2), max(y1, y2) + 1):
                if self.grid[y][x1] in danger + [dir_char] and (x1, y) != (x2, y2):
                    return False
            return True
    
    def _place_link_info(
            self, x: int, y: int, info: str) -> None:
        """
        """
        mid = len(info) // 2
        for i, char in enumerate(info):
            x_pos = x + i - mid
            if 0 <= x_pos <= self.col and 0 <= y <= self.row:
                self.grid[y][x + i - mid] = char
    
    def _colored_char(c: str, color: str) -> str:
        """
        """
        try:
            color_code = style(color)
            reset = style("reset")
            return f"{color_code}{c}{reset}"
        
        except Exception:
            return c
    
    def print_map(self) -> None:
        for y, row in enumerate(self.grid):
            for x, char in enumerate(row):
                print(char, end="")
            print()

