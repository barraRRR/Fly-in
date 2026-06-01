from class_network import Network, Hub, HubType
from typing import List, Dict, Tuple


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

                info = self._get_link_info(hub, dest)
                self._draw_smart_line(hub, dest, info)
    
    def _draw_horizontal_line(
            self,
            x1: int, x2: int,
            y: int,
            left_char: str = "●",
            right_char: str = "●",
            info: str = None) -> Tuple[int, int]:
        """
        """
        for x in range(min(x1, x2), max(x1, x2) + 1):
            if 1 < x < self.col - 1 and 1 < y < self.row - 1:
                if self.grid[y][x] != " ":
                    continue
                if x == x1:
                    self.grid[y][x] = left_char
                elif x == x2:
                    self.grid[y][x] = right_char
                else:
                    self.grid[y][x] = "─"
        
        if info is not None:
            midway = (x1 + x2) // 2
            self._place_link_info(midway, y, info)
        
        return (x, y)
    
    def _draw_vertical_line(
            self,
            x: int,
            y1: int, y2: int,
            top_char: str = "●",
            bottom_char: str = "●",
            info: str = None) -> Tuple[int, int]:
        """
        """
        for y in range(min(y1, y2), max(y1, y2) + 1):
            if 1 < x < self.col - 1 and 1 < y < self.row - 1:
                if self.grid[y][x] == "─":
                    self.grid[y][x] = "┼"
                elif self.grid[y][x] != " ":
                    continue
                if y == y1:
                    self.grid[y][x] = top_char
                elif y == y2:
                    self.grid[y][x] = bottom_char
                else:
                    self.grid[y][x] = "│"
        
        if info is not None:
            midway = (y1 + y2) // 2
            self._place_link_info(x, midway, info)

        
        return (x, y2)
    
    def _draw_gentle_exit(
            self,
            x1: int, y1: int,
            exit: bool,
            length: int = 4) -> Tuple[int, int]:
        """
        """
        self.grid[y1][x1] = "●"
        step = 1 if exit else -1
        for x in range(x1 + step, x1 + length * step, step):
            if 1 < x < self.col - 1 and 1 < y1 < self.row - 1:
                if self.grid[y1][x] != " ":
                    continue
                else:
                    self.grid[y1][x] = "─"
        
        return (x1 + (length * step), y1)
    
    def _draw_s_line(
            self, x1: int, x2: int, y1: int, y2: int, info: str) -> None:
        """
        """
        midway = (y2 - y1) // 2
        up = ["┘", "┐", "└", "┌"]
        down = ["┐", "┘", "┌", "└"]
        dir = up if y2 < y1 else down

        x1, y1 = self._draw_vertical_line(x1, y1, y1 + midway, dir[0], dir[1])
        x1, y1 = self._draw_horizontal_line(x1, x2, y1, dir[1], dir[2], info)
        self._draw_vertical_line(x1, y1, y2, dir[2], dir[3])
    
    def _draw_z_line(
            self, x1: int, x2: int, y1: int, y2: int, info: str) -> None:
        """
        """
        midway = (x2 - x1) // 2
        up_right = ["┘", "┌"]
        up_left = ["└", "┐"]
        down_right = ["┐", "└"]
        down_left = ["┌", "┘"]
        circle_rigth = ["┐", "┘"]
        
        if y2 < y1 and x1 < x2:
            dir = up_right
        elif y2 < y1 and x1 > x2:
            dir = up_left
        elif y2 > y1 and x1 < x2:
            dir = down_right
        elif x1 == x2:
            dir = circle_rigth
        else:
            dir = down_left

        if (x2 - x1) >= (y2 - y1):
            x1, y1 = self._draw_horizontal_line(
                x1, x2, y1, "─", dir[0], info
                )
            x1, y1 = self._draw_vertical_line(
                x1, y1, y2, dir[0], dir[1]
                )
        else:
            x1, y1 = self._draw_vertical_line(
                x1, y1, y2, dir[0], dir[1], info
                )
            x1, y1 = self._draw_horizontal_line(
                x1, x2, y1, "─", dir[0]
                )
        #self._draw_horizontal_line(x1, x2, y1, dir[1], "─")
    
    def _draw_smart_line(
            self,
            hub_a: Hub,
            hub_b: Hub,
            info: str) -> None:
        """
        """
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

        (left_x, left_y), (right_x, right_y) = sorted([(x1, y1), (x2, y2)])
        
        x1, y1 = self._draw_gentle_exit(left_x, left_y, exit=True)
        x2, y2 = self._draw_gentle_exit(right_x, right_y, exit=(left_x == right_x))

        if y1 == y2:
            self._draw_horizontal_line(x1, x2, y1, "─", "─", info)
        
        """
        elif x1 > x2:
            self._draw_s_line(x1, x2, y1, y2, info)
        else:
        """
        self._draw_z_line(x1, x2, y1, y2, info)
        
    def _get_link_info(self, hub_a: Hub, hub_b: Hub) -> str:
        """
        """
        for link in hub_a.links:
            if link['target_hub'] == hub_b:
                max_connections = link['max']
                incoming = link['incoming_drones']
                return f"{incoming}/{max_connections}"
        return ""
    
    def _place_link_info(
            self, x: int, y: int, info: str) -> None:
        """
        """
        mid = len(info) // 2
        for i, char in enumerate(info):
            x_pos = x + i - mid
            if 0 <= x_pos <= self.col and 0 <= y <= self.row:
                self.grid[y][x + i - mid] = char
    
    def print_map(self) -> None:
        for row in self.grid:
            print("".join(row))
