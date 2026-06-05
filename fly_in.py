from class_network import Network, Drone, Hub
from class_parser import MapParser
from class_simulator import Simulator
from class_gui import Gui
from utils import clear, menu, wait_for_enter, select_map_file, welcome, goodbye, slice_str, PACE, FAST, DELAY, STATUS, WARNING, UX_MAX, UX_STD, UX
from typing import List
from time import sleep
import sys
import utils


def main() -> None:
    welcome()
    while True:
        while True:
            map_file = select_map_file()
            if map_file is None:
                goodbye()
            map = MapParser(map_file)
            net = Network(**map.data)
            sim = Simulator(net)
            gui = Gui(net)
            if confirm_map(gui, map_file):
                break
        
        manual = False
        config = configure_ux(gui)
        if config == 0:
            utils.PACE = DELAY
            manual = True
        elif config == 1:
            utils.PACE = DELAY
            manual = False
        else:
            utils.PACE = utils.FAST
            manual = False

        turn_list: List[str] = []
        drone_status: List[str] = []
        pannel: str = ""
        frame = 0
        try:
            while sim.drones_left:
                refresh(gui, sim, pannel)
                for event in sim.simulate_turn():
                    frame += 1
                    if event["type"] == "drone_status":
                        drone_status.insert(0, event["msg"])
                    elif event["type"] == "end_turn":
                        drone_status.insert(0, f"[END OF TURN {sim.turn_num:03d}]")
                        turn_list.insert(0, event["msg"])
                    
                    gui.update(frame)
                    pannel = text_pannel(
                        net=net,
                        sim=sim,
                        gui=gui,
                        col_left=drone_status,
                        col_right=turn_list
                    )
                    refresh(gui, sim, pannel)
                    sleep(utils.PACE)
                    
                    if manual and event["type"] == "end_turn" and sim.drones_left:
                            print()
                            wait_for_enter()
                    

            print(f"\n{UX['success']}\n".center(gui.col if gui.col < UX_MAX else UX_STD))
        except KeyboardInterrupt:
            pass
        
        print("\n\n")
        idx = menu(["New simulation", "Exit"])
        if idx == 0:
            continue
        else:
            goodbye()


def confirm_map(gui: Gui, map_file: str) -> bool:
    """
    """
    clear()
    col = gui.col if gui.col < UX_MAX else UX_STD
    map_name = map_file.split("/")[-1].removesuffix(".txt")
    print("\n" + "═" * col)
    print("CONFIRM MAP".center(col))
    print("═" * col, end="\n\n")
    print("Map name: " + map_name, end="\n\n")
    if gui.col < UX_MAX:
        gui.print_map()
    else:
        print(UX["size_warning"])
    print()
    options = ["Continue", "Select a different map", "❌ Exit"]
    idx = menu(options)
    if idx == 0:
        return True
    if idx == 1:
        return False
    else:
        goodbye()


def configure_ux(gui: Gui) -> int:
    """
    """
    col = gui.col if gui.col < UX_MAX else UX_STD
    print("\n" + "═" * col)
    print("CONFIGURE SIMULATION".center(col))
    print("═" * col, end="\n\n")
    idx = menu(["Manual", "Automatic", "Direct to the point"])
    return idx



def refresh(gui: Gui, sim: Simulator, pannel: str) -> None:
    """
    """
    clear()
    if gui.col < UX_MAX:
        gui.print_map()
    print(info_panel(gui, sim))
    print(pannel)
    # print(f"\n{UX['interrupt_hint']}")


def info_panel(
        gui: Gui,
        sim: Simulator,
        margin: int = 6) -> str:
    """
    """
    col = gui.col if gui.col < UX_MAX else UX_STD
    sub_size = col // 2 - (margin // 2)
    title = " STATUS ".center(col, "=")
    info_drones = f"Drones left: {len(sim.drones_left)}".center(col)
    info_turns = f"Total turns: {sim.turn_num}".center(col)
    bottom = "".center(col, "=")

    def place_subtitle(sub1: str, sub2: str, size: int, margin: int) -> str:
        return (
            "┌" + "─" * (size - 2) + "┐" +
            " " * margin +
            "┌" + "─" * (size - 2) + "┐\n" +
            "|" + sub1.center(size - 2) + "|" +
            " " * margin +
            "|" + sub2.center(size - 2) + "|\n" +
            "└" + "─" * (size - 2) + "┘" +
            " " * margin +
            "└" + "─" * (size - 2) + "┘\n"
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
    col = gui.col if gui.col < UX_MAX else UX_STD
    max_lines = 10
    row = max_lines
    max_char_line = col // 2 - (margin // 2)
    
    col_left = slice_str(col_left, max_char_line, max_lines)
    col_right = slice_str(col_right, max_char_line, max_lines)

    grid = [[" " for _ in range(col)] for _ in range(row)]

    for y, line in enumerate(col_left):
        if y >= row:
            break
        for x, char in enumerate(line):
            if x >= max_char_line:
                break
            grid[y][x] = char

    off = max_char_line + margin

    for y, line in enumerate(col_right):
        if y >= row:
            break
        for x, char in enumerate(line):
            if x >= max_char_line:
                break
            grid[y][x + off] = char
    
    return "\n".join(["".join(row) for row in grid])


if __name__ == "__main__":
    main()

