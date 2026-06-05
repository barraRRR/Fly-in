from class_network import Network, Hub, HubType
from typing import List, Dict, Tuple, Set
from blessed import Terminal
from utils import drone_helices


class Gui:
    """
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
        "line": "#FFFFFF"
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
        height = (max_y - min_y + 1) * (self.HUB_HEIGHT + self.METADATA_HEIGHT) + self.MARGIN * 2
        
        self.col, self.row = width, height
        self.grid: List[List[Dict[str, str | None]]] = [[{"char": " ", "color": None} for _ in range(self.col)] for _ in range(self.row)]
        self.grid_block: Set[Tuple[int, int]] = Set()
        self.hub_pos_map: Dict[Hub, Tuple[int,int]] = {}

        self.corners = ["─", "┌", "┐", "└", "┘"]
        self.hor_line = "─"
        self.ver_line = "│"
        self.point = "■"
        self.cross = "┼"

        self.term = Terminal()
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
            
            meta_lines = self._hub_metadata(hub)
            for i, line in enumerate(meta_lines):
                row = grid_y + 3 + i
                if row < self.row - 1:
                    for j, char in enumerate(line):
                        col = grid_x + j
                        if col < self.col - 1:
                            self.grid[row][col]["char"] = char
                            self.grid[row][col]["color"] = self.PALETTE["drone_color"] if char == "●" else None
                            if not char.isspace():
                                self.grid_block.add((col, row))


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

                # traffic
                while self.grid[y1][x1]["char"] == "■":
                    y1 -= 1
                while self.grid[y2][x2]["char"] == "■":
                    y2 -= 1

                self.grid[y1][x1]["char"], self.grid[y2][x2]["char"] = "■", "■"

                line = self._find_line(x1, y1, x2, y2)
                self._fill_line(line, info, frame)
                self.grid_block.add((x1, y1), (x2, y2))

    def _find_line(
            self,
            x1: int, y1: int,
            x2: int, y2: int,
            visited: Set[Tuple[int, int]] = None,
            path: List[Tuple[int, int]] = None,
            ) -> List[Tuple[int, int]]:
        """
        Encuentra un camino libre de obstáculos mediante DFS (Depth-First Search)
        """
        if visited is None:
            visited = set()
        if path is None:
            path = []

        if (x1, y1) == (x2, y2):
            return path + [(x1, y1)]

        # Marcamos la celda actual como visitada para no entrar en bucles infinitos
        visited.add((x1, y1))
        current_path = path + [(x1, y1)]

        abs_dx = abs(x2 - x1)
        abs_dy = abs(y2 - y1)
        dx = 1 if x2 > x1 else (-1 if x2 < x1 else 0)
        dy = 1 if y2 > y1 else (-1 if y2 < y1 else 0)

        # Ordenamos los posibles movimientos dando prioridad a la dirección que más nos acerque al objetivo
        moves = []
        if abs_dx >= abs_dy:
            if dx != 0: moves.append((x1 + dx, y1))
            if dy != 0: moves.append((x1, y1 + dy))
            if dy == 0: moves.extend([(x1, y1 + 1), (x1, y1 - 1)]) # Intentar rodear si estamos alineados en Y
            if dx != 0: moves.append((x1 - dx, y1))
            if dy != 0: moves.append((x1, y1 - dy))
        else:
            if dy != 0: moves.append((x1, y1 + dy))
            if dx != 0: moves.append((x1 + dx, y1))
            if dx == 0: moves.extend([(x1 + 1, y1), (x1 - 1, y1)]) # Intentar rodear si estamos alineados en X
            if dy != 0: moves.append((x1, y1 - dy))
            if dx != 0: moves.append((x1 - dx, y1))

        for nx, ny in moves:
            if (nx, ny) not in visited and (nx, ny) not in self.grid_block:
                # Asegurarse de no salir de los límites de la terminal (opcional, pero buena práctica)
                if 0 <= nx < self.col and 0 <= ny < self.row:
                    is_valid = True
                    
                    # Evitar giros sobre líneas existentes para asegurar que solo se cruzan perpendicularmente
                    current_char = self.grid[y1][x1]["char"]
                    if current_char == "│" and nx == x1: # Si estamos sobre una vertical, no podemos movernos verticalmente
                        is_valid = False
                    elif current_char == "─" and ny == y1: # Si estamos sobre una horizontal, no podemos movernos horizontalmente
                        is_valid = False
                        
                    # Comprobar la celda de destino para evitar solapamientos
                    if is_valid and (nx, ny) != (x2, y2):
                        target_char = self.grid[ny][nx]["char"]
                        if nx != x1 and target_char not in [" ", "│"]:
                            is_valid = False
                        elif nx == x1 and target_char not in [" ", "─"]:
                            is_valid = False

                    if is_valid:
                        result = self._find_line(nx, ny, x2, y2, visited, current_path)
                        if result:
                            return result # Devolvemos el primer camino válido encontrado

        return [] # Retorna vacío si no hay camino posible desde este punto (provoca backtracking)

    def _fill_line(self, line: List[Tuple[int, int]], info: str = None, frame: int = 0) -> None:
        """
        """
        # Iteramos desde el segundo elemento hasta el penúltimo para evitar desbordamientos
        for i in range(1, len(line) - 1):
            px, py = line[i - 1] # Punto anterior
            dx, dy = line[i]     # Punto actual
            nx, ny = line[i + 1] # Punto siguiente

            # Detectamos en qué direcciones están los dos puntos adyacentes
            left = (px < dx) or (nx < dx)
            right = (px > dx) or (nx > dx)
            up = (py < dy) or (ny < dy)
            down = (py > dy) or (ny > dy)

            # Elegimos el carácter según la combinación de direcciones
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
                continue # Por si acaso se cruzan o hay solapamiento inesperado
                
            # Si la celda está vacía, dibujamos el carácter de nuestra ruta.
            # Si ya hay un carácter (estamos cruzando otra línea), no lo sobreescribimos
            # para crear la ilusión de que nuestra línea actual pasa "por debajo".
            if self.grid[dy][dx]["char"] == " ":
                self.grid[dy][dx]["char"] = char
                self.grid[dy][dx]["color"] = self.PALETTE["line"]

            if i == len(line) // 2:
                self._place_link_info(dx, dy, info, frame)
                
    def _place_drone(self, x: int, y: int, frame: int = 0) -> str:
        """
        """
        drone1 = "+♦+"
        drone2 = "✕♦✕"
        
        selected = drone1 if frame % 2 == 0 else drone2

        for c in range(len(selected)):
            self.grid[y][x + c]["char"] = selected[c]
            self.grid[y][x + c]["color"] = self.PALETTE["drone_color"]

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

    def _get_colored_char(self, c: str, color: str) -> str:
        """
        """
        try:
            if color.startswith("#"):
                color_code = self.term.color_hex(color)
            else:
                color_code = getattr(self.term, color.lower(), self.term.normal)
            return f"{color_code}{c}{self.term.normal}"
        
        except Exception as e:
            return c

    def print_map(self) -> None:
        """
        """
        for row in self.grid:
            for c in row:
                print(self._get_colored_char(c["char"], c["color"]), end="")
            print()
