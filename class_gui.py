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
        
        # Calcular rango de coordenadas
        min_x = min(hub.coords[0] for hub in self.all_hubs)
        max_x = max(hub.coords[0] for hub in self.all_hubs)
        min_y = min(hub.coords[1] for hub in self.all_hubs)
        max_y = max(hub.coords[1] for hub in self.all_hubs)
        
        self.min_x = min_x
        self.min_y = min_y
        
        # Calcular dimensiones del grid
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
        Retorna las líneas de metadata del hub centradas.
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
        Dibuja los hubs y sus metadatos en el grid.
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
        hub_dict = {hub.name: hub for hub in self.all_hubs}

        for connection in self.net.connections:
            hub_a_name = connection["point_a"]
            hub_b_name = connection["point_b"]
    
            hub_a = hub_dict.get(hub_a_name)
            hub_b = hub_dict.get(hub_b_name)

            if hub_a and hub_b:
                self._draw_line(hub_a, hub_b)
    
    def _get_link_info(self, hub_a: Hub, hub_b: Hub) -> str:
        """
        Retorna la información de la conexión entre dos hubs.
        Formato: "3/5" (conexiones_libres/max_conexiones)
        """
        for link in hub_a.links:
            if link['target_hub'] == hub_b:
                max_connections = link['max']
                incoming = link['incoming_drones']
                return f"{incoming}/{max_connections}"
        return ""
    
    def _draw_line(self, hub_a: Hub, hub_b: Hub) -> None:
        """
        Dibuja una línea conectando los bordes de dos hubs.
        La línea skipea caracteres no-espacios para no sobrescribir hubs/metadata.
        """
        grid_x1, grid_y1 = self.hub_pos_map[hub_a]
        grid_x2, grid_y2 = self.hub_pos_map[hub_b]
        
        # Puntos de conexión en los bordes de los hubs
        hub_height_center = grid_y1 + 1  # Segunda fila (y + 1)
        
        # Determinar si hub_a está a la izquierda o derecha de hub_b
        if grid_x1 < grid_x2:
            # hub_a a la izquierda, hub_b a la derecha
            x1 = grid_x1 + 13  # Link derecho de hub_a
            x2 = grid_x2 + 6   # Link izquierdo de hub_b
        else:
            # hub_a a la derecha, hub_b a la izquierda
            x1 = grid_x1 + 6   # Link izquierdo de hub_a
            x2 = grid_x2 + 13  # Link derecho de hub_b
        
        y1 = hub_height_center
        y2 = grid_y2 + 1  # Centro vertical de hub_b

        self._draw_simple_horizontal_line(x1, x2, y1, y2)
        
        # Dibujar línea vertical (empieza desde el siguiente punto después de la horizontal)
        step = 1 if y1 < y2 else -1
        for y in range(y1 + step, y2 + step, step):
            if 1 < x2 < self.col - 1 and 1 < y < self.row - 1:
                # Si el espacio no está vacío, skipea (no sobrescribe)
                if self.grid[y][x2] != " ":
                    continue
                # Si está vacío, usa tubería
                else:
                    self.grid[y][x2] = "│"
        
        # Dibuja la bolita final
        if 1 < x2 < self.col - 1 and 1 < y2 < self.row - 1:
            self.grid[y2][x2] = "●"
        
        # Dibuja la información de conexiones a mitad de la línea horizontal (debajo)
        x_mid = (min(x1, x2) + max(x1, x2)) // 2
        link_info = self._get_link_info(hub_a, hub_b)
        if link_info:
            y_info = y1 + 1  # Debajo de la línea horizontal
            
            # Centrar el texto alrededor del punto medio
            info_start = x_mid - len(link_info) // 2
            
            for i, char in enumerate(link_info):
                x_pos = info_start + i
                if 1 < x_pos < self.col - 1 and 1 < y_info < self.row - 1:
                    # Solo dibuja si el espacio está vacío
                    if self.grid[y_info][x_pos] == " ":
                        self.grid[y_info][x_pos] = char
    
    def _draw_simple_horizontal_line(
            self,
            x1: int, x2: int,
            y1: int, y2: int,
            left_char: str = "●",
            right_char: str = "●") -> None:
        """
        """
        # Dibujar línea horizontal
        for x in range(min(x1, x2), max(x1, x2) + 1):
            if 1 < x < self.col - 1 and 1 < y1 < self.row - 1:
                # Si es el punto inicial o final, usa bolita
                if x == x1:
                    self.grid[y1][x] = left_char
                if x == x2:
                    self.grid[y1][x] = right_char
                # Si el espacio no está vacío, skipea (no sobrescribe)
                elif self.grid[y1][x] != " ":
                    continue
                # Si está vacío, usa guión
                else:
                    self.grid[y1][x] = "─"
    
    def print_map(self) -> None:
        for row in self.grid:
            print("".join(row))
