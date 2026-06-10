from class_network import Network
from class_parser import MapParser
from class_simulator import Simulator
from class_gui import Gui
from utils import clear, menu, wait_for_enter, select_map_file
from utils import welcome, goodbye, DELAY, STATUS, ERROR, UX_MAX, UX_STD, UX
from typing import List
from time import sleep
from pydantic import ValidationError
import utils
import sys


__author__ = "Javier Barreiro"
__email__ = "jbarreir@student.42madrid.com"


def main() -> None:
    """Main execution loop handling application state and interactive flow."""

    map_arg = None
    if len(sys.argv) == 2:
        map_arg = sys.argv[1]

    elif len(sys.argv) > 2:
        clear()
        print(ERROR["critical"]["usage"])
        sys.exit(1)

    welcome()
    while True:
        while True:
            try:
                map_file = map_arg if map_arg else select_map_file()
                map_arg = None
                if map_file is None:
                    goodbye()
                map_path = str(map_file)
                map = MapParser(map_path)
                map_name = map.data["map"]
                net = Network(**map.data)
                sim = Simulator(net)
                gui = Gui(net)
                if confirm_map(gui, map_name):
                    break

            except ValidationError as e:
                clear()
                print(ERROR["parser"]["parsing_error"])
                for error in e.errors():
                    field_loc = " -> ".join(str(loc) for loc in error["loc"])
                    display_loc = (
                        field_loc if field_loc else "Map Configuration"
                    )
                    print(f"   └── [{display_loc}] {error['msg']}\n")
                wait_for_enter(None)
                continue

            except ValueError as e:
                clear()
                print(ERROR["parser"]["parsing_error"])
                print(f"   └── {e}\n")
                wait_for_enter(None)
                continue

            except Exception as e:
                clear()
                print(f"CRITICAL ERROR: {e}\n")
                wait_for_enter(None)
                goodbye()

        manual = False
        direct = False
        config = configure_ux(gui)
        if config == 0:
            utils.PACE = DELAY
            manual = True
        elif config == 1:
            utils.PACE = DELAY
        elif config == 2:
            utils.PACE = utils.FAST
        else:
            utils.PACE = utils.DIRECT
            direct = True
            clear()
            gui.col = UX_STD
            print(UX["simulation_ongoing"])

        turn_list: List[str] = []
        drone_status: List[str] = []
        col_left: List[str] = []
        col_right: List[str] = []
        frame = 0

        def refresh(
            gui: Gui,
            sim: Simulator,
            col_left: List[str],
            col_right: List[str],
            map_name: str,
        ) -> None:
            """Refreshes the GUI elements safely during simulation runtime.

            Args:
                gui (Gui): The main graphical interface instance.
                sim (Simulator): The active simulator instance.
                col_left (List[str]): Drone status event log records.
                col_right (List[str]): Turn completion logs.
                map_name (str): Current active map name.
            """
            clear()
            gui._place_map_name(map_name)
            if gui.col < UX_MAX:
                gui.print_grid(gui.grid)

            sim_drones_left = len(sim.drones_left)
            sim_turn_num = int(sim.metrics["current_turn"])
            gui._text_pannel(
                drones_left=sim_drones_left,
                col_left=col_left,
                col_right=col_right,
                map_name=map_name,
                turn_num=sim_turn_num
            )

        try:
            while sim.drones_left:
                if not direct:
                    refresh(gui, sim, col_left, col_right, map_name)

                for event in sim.simulate_turn():
                    frame += 1
                    if event["type"] == "drone_status":
                        drone_status.insert(0, event["msg"])
                    elif event["type"] == "end_turn":
                        drone_status.insert(
                            0,
                            STATUS["end_of_turn"].format(
                                turn_num=sim.metrics["current_turn"]
                            ),
                        )
                        turn_list.insert(0, event["msg"])

                    if not direct:
                        gui.update(frame)
                    col_left = drone_status
                    col_right = turn_list

                    if not direct:
                        refresh(gui, sim, col_left, col_right, map_name)
                    sleep(utils.PACE)

                    if (
                        manual
                        and event["type"] == "end_turn"
                        and sim.drones_left
                        and not direct
                    ):
                        print()
                        wait_for_enter(None)

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
    """Prompts the user to review and confirm the loaded map.

    Args:
        gui (Gui): Interface containing the rendered map.
        map_name (str): Chosen map identifier.

    Returns:
        bool: True if confirmed, False to return to map selection.
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
    return False


def configure_ux(gui: Gui) -> int:
    """Displays UX configuration menus for speed adjustments.

    Args:
        gui (Gui): Active GUI instance for column centering.

    Returns:
        int: Selected configuration index (e.g., manual, automatic, fast).
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
            UX["mode_direct"],
        ]
    )
    return idx


if __name__ == "__main__":
    main()
