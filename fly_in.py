from class_network import Network, Drone, Hub
from class_parser import MapParser
from class_simulator import Simulator
from class_gui import Gui
from utils import clear, DELAY, STATUS, WARNING
from typing import List
from time import sleep
from textwrap import wrap

"""
map = MapParser("./maps/easy/01_linear_path.txt")
print(map.data)
net = Network(**map.data)
print(net.get_map_info())
"""


def main() -> None:
    map = MapParser("./maps/medium/01_dead_end_trap.txt")
    net = Network(**map.data)
    sim = Simulator(net)
    gui = Gui(net)
    turn_list: List[str] = []
    drone_status: List[str] = []
    pannel: str = ""
    while sim.drones_left:
        refresh(gui, sim, pannel)
        for event in sim.simulate_turn():
            if event["type"] == "drone_status":
                drone_status.insert(0, event["msg"])
            elif event["type"] == "end_turn":
                drone_status.insert(0, f"[END OF TURN {sim.turn_num:03d}]")
                turn_list.insert(0, event["msg"])
            
            gui.update()
            pannel = text_pannel(
                net=net,
                sim=sim,
                gui=gui,
                col_left=drone_status,
                col_right=turn_list
            )
            refresh(gui, sim, pannel)
            sleep(DELAY)


def refresh(gui: Gui, sim: Simulator, pannel: str) -> None:
    """
    """
    clear()
    gui.print_map()
    print(info_panel(gui, sim))
    print(pannel)


def info_panel(gui: Gui, sim: Simulator, margin: int = 6) -> str:
    """
    """
    col = gui.col
    sub_size = col // 2 - (margin // 2)
    title = " STATUS ".center(col, "=")
    info_drones = f"Drones left: {len(sim.drones_left)}".center(col)
    info_turns = f"Total turns: {sim.turn_num}".center(col)
    bottom = "".center(col, "=")

    def place_subtitle(sub1: str, sub2: str, size: int, margin: int) -> str:
        return (
            "┌" + "-" * (size - 2) + "┐" +
            " " * margin +
            "┌" + "-" * (size - 2) + "┐\n" +
            "|" + sub1.center(size - 2) + "|" +
            " " * margin +
            "|" + sub2.center(size - 2) + "|\n" +
            "└" + "-" * (size - 2) + "┘" +
            " " * margin +
            "└" + "-" * (size - 2) + "┘\n"
            )
    subtitles = place_subtitle("DRONE LOG", "TURN LOG", sub_size, margin)

    return "\n".join([title, info_drones, info_turns, bottom, subtitles])

        
def text_pannel(net: Network,
                sim: Simulator,
                gui: Gui,
                col_left: List[str],
                col_right: List[str],
                margin: int = 6) -> str:
    """
    """
    col, row = gui.col, gui.row
    max_lines = 10
    max_char_line = col // 2 - (margin // 2)
    
    col_left = slice_str(col_left, max_char_line, max_lines)
    col_right = slice_str(col_right, max_char_line, max_lines)

    grid = [[" " for _ in range(col)] for _ in range(row)]

    for y, line in enumerate(col_left):
        if y >= row:  # ← VALIDACIÓN: no salirse del grid
            break
        for x, char in enumerate(line):
            if x >= max_char_line:  # ← VALIDACIÓN: no salirse del ancho
                break
            grid[y][x] = char

    off = max_char_line + margin

    for y, line in enumerate(col_right):
        if y >= row:  # ← VALIDACIÓN: no salirse del grid
            break
        for x, char in enumerate(line):
            if x >= max_char_line:  # ← VALIDACIÓN: no salirse del ancho
                break
            grid[y][x + off] = char
    
    return "\n".join(["".join(row) for row in grid])


def slice_str(str_list: List[str], max_char_line: int, max_lines: int) -> List[str]:
    """
    """
    str_list = str_list[:max_lines]
    new = [line for s in str_list for line in wrap(s, max_char_line)]
    return new
    

if __name__ == "__main__":
    main()

