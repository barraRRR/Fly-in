from class_network import Network
from typing import List


class Gui:
    """
    """
    UX_SIZE = (160, 40)
    def __init__(self, net: Network) -> None:
        self.net = net
        self.col, self.row = self.UX_SIZE
        self.grid: List[List[str]] = [[" " for _ in range(self.col)] for _ in range(self.row)]
        self._map_contour()
    
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
    
    def print_map(self) -> None:
        for row in self.grid:
            print("".join(row))