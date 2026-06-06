from class_network import Network
from class_parser import MapParser
from class_simulator import Simulator
from class_gui import Gui
from utils import (
    clear, menu, wait_for_enter, select_map_file, welcome, goodbye,
    slice_str, PACE, FAST, DIRECT, DELAY, STATUS, WARNING, UX_MAX, UX_STD, UX
)
from typing import List
from time import sleep
import sys
import utils


def main() -> None:
    """Main execution loop for the Fly-In program.
    Handles application state and interactive flow.
    """
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
                print(ERROR["parser"]["parsing_error"])
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
        elif config == 2:
            utils.PACE = utils.FAST
            manual = False
        else:
            utils.PACE = utils.DIRECT
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
            """Refreshes the GUI elements safely during
            the simulation runtime.

            Args:
                gui (Gui): The main graphical interface instance.
                sim (Simulator): The active simulator instance
                with current turn data.
                col_left (List[str]): Drone status event log records.
                col_right (List[str]): Turn completion logs.
                map_name (str): Current active map name.
            """
            clear()
            gui._place_map_name(map_name)
            if gui.col < UX_MAX:
                gui.print_grid(gui.grid)

            gui._text_pannel(
                drones_left=sim.drones_left,
                col_left=col_left,
                col_right=col_right,
                map_name=map_name,
                turn_num=sim.metrics["current_turn"])

        try:
            while sim.drones_left:                
                refresh(gui, sim, col_left, col_right, map_name)

                for event in sim.simulate_turn():
                    frame += 1
                    if event["type"] == "drone_status":
                        drone_status.insert(0, event["msg"])
                    elif event["type"] == "end_turn":
                        drone_status.insert(
                            0, STATUS["end_of_turn"].format(
                                turn_num=sim.metrics["current_turn"]
                                ))
                        turn_list.insert(0, event["msg"])

                    gui.update(frame)
                    col_left = drone_status
                    col_right = turn_list

                    refresh(gui, sim, col_left, col_right, map_name)
                    sleep(utils.PACE)

                    if (manual and 
                        event["type"] == "end_turn"
                        and sim.drones_left):
                        print()
                        wait_for_enter()
            
            sim._get_metrics()
            gui._metrics_panel(sim.metrics)

        except KeyboardInterrupt:
            pass

        print("\n\n")
        idx = menu([UX["new_simulation"], UX["exit_simple"]])
        if idx == 0:
            continue
        else:
            goodbye()


def confirm_map(gui: Gui, map_name: str) -> bool:
    """Prompts the user to review and confirm
    the loaded map before simulation begins.

    Args:
        gui (Gui): The graphical interface containing
        the rendered map representation.
        map_name (str): Chosen map identifier.

    Returns:
        bool: True if the user confirms the map,
        False to return to map selection.
    """
    clear()
    col = gui.col if gui.col < UX_MAX else UX_STD
    print("\n" + "═" * col)
    print(UX["confirm_map"].center(col))
    print("═" * col, end="\n\n")
    print(UX["map_name"].format(map_name=map_name), end="\n\n")
    if gui.col < UX_MAX:
        gui.print_grid(gui.grid)
    else:
        print(UX["size_warning"])
    print()
    options = [UX["continue_sim"], UX["select_diff_map"], UX["exit_option"]]
    idx = menu(options)
    if idx == 0:
        return True
    if idx == 1:
        return False
    else:
        goodbye()


def configure_ux(gui: Gui) -> int:
    """Displays user experience configuration menus,
    allowing speed and verbosity adjustments.

    Args:
        gui (Gui): The active GUI instance to compute column
        centering based on window size.

    Returns:
        int: The selected configuration index (e.g., manual, automatic, fast).
    """
    col = gui.col if gui.col < UX_MAX else UX_STD
    print("\n" + "═" * col)
    print(UX["configure_sim"].center(col))
    print("═" * col, end="\n\n")
    idx = menu(
        [
            UX["mode_manual"],
            UX["mode_auto"],
            UX["mode_fast"],
            UX["mode_direct"]
            ])
    return idx


if __name__ == "__main__":
    main()
