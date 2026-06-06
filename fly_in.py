from class_network import Network
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
            try:
                map_file = select_map_file()
                if map_file is None:
                    goodbye()
                map_name = map_file.split("/")[-1].removesuffix(".txt")
                map = MapParser(map_file)
                net = Network(**map.data)
                sim = Simulator(net)
                gui = Gui(net)
                if confirm_map(gui, map_name):
                    break
            
            except ValueError:
                print("ERROR: Error parsing map file")
                wait_for_enter()
                continue
        
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
        col_left = []
        col_right = []
        frame = 0

        def refresh(
                gui: Gui,
                sim: Simulator,
                col_left: List[str],
                col_right: List[str],
                map_name: str) -> None:
            """
            """
            clear()
            gui._place_map_name(map_name)
            if gui.col < UX_MAX:
                gui.print_grid(gui.grid)

            gui._text_pannel(
                sim.drones_left,
                sim.turn_num,
                col_left,
                col_right,
                map_name)

        try:
            while sim.drones_left:                
                refresh(gui, sim, col_left, col_right, map_name)

                for event in sim.simulate_turn():
                    frame += 1
                    if event["type"] == "drone_status":
                        drone_status.insert(0, event["msg"])
                    elif event["type"] == "end_turn":
                        drone_status.insert(0, f"[END OF TURN {sim.turn_num:03d}]")
                        turn_list.insert(0, event["msg"])
                    
                    gui.update(frame)
                    col_left = drone_status
                    col_right = turn_list
                    
                    refresh(gui, sim, col_left, col_right, map_name)
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


def confirm_map(gui: Gui, map_name: str) -> bool:
    """
    """
    clear()
    col = gui.col if gui.col < UX_MAX else UX_STD
    print("\n" + "═" * col)
    print("CONFIRM MAP".center(col))
    print("═" * col, end="\n\n")
    print("Map name: " + map_name, end="\n\n")
    if gui.col < UX_MAX:
        gui.print_grid(gui.grid)
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


if __name__ == "__main__":
    main()
