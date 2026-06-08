from typing import Tuple, Dict, List, Union, Optional, Generator, Any
from itertools import count
from pathlib import Path
from simple_term_menu import (  # type: ignore[import-untyped, unused-ignore]
    TerminalMenu,
)
from textwrap import wrap
import sys
import os
import json


def import_texts(
    language: str,
) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    """Imports application texts safely from a JSON file.

    Args:
        language (str): Locale code (e.g., 'en').

    Returns:
        Tuple[Dict, Dict, Dict, Dict]: UX, status, warnings, errors.
    """
    file = f"{language}_texts.json"

    try:
        print("Loading texts...", end="")
        with open(file, "r") as raw:
            texts = json.load(raw)
            print(" OK")
            return (
                texts["ux"],
                texts["status"],
                texts["warning"],
                texts["error"],
            )

    except FileNotFoundError as e:
        print(" FAIL")
        print(f"CRITICAL ERROR: {e}")
        sys.exit("Aborting launch...")


UX, STATUS, WARNING, ERROR = import_texts("en")
UX_MAX: int = 500
UX_STD: int = 100
DELAY: float = 0.5
FAST: float = 0.1
DIRECT: float = 0.0
PACE = DELAY
path_id_generator = count(1)
drone_helices = count(1)


def clear() -> None:
    """Clears the console or terminal screen cleanly."""
    os.system("cls" if os.name == "nt" else "clear")


def menu(items: List[str]) -> int:
    """Deploys an interactive terminal UI menu.

    Args:
        items (List[str]): List of textual options to display.

    Returns:
        int: Index of the selected string, or -1 if cancelled.
    """
    menu_obj = TerminalMenu(
        items,
        title="Use ↑ ↓ arrows to navigate, ENTER to select",
        menu_cursor="➜ ",
        menu_cursor_style=("fg_cyan", "bold"),
        show_search_hint=False,
    )
    idx = menu_obj.show()
    return idx if idx is not None else -1


def select_map_file() -> Union[str, None]:
    """Invokes a visual tool enabling users to pick a `.txt` map.

    Returns:
        str: File path pointing to the selected map.
    """
    maps_root = Path(".")
    current_dir = maps_root

    while True:
        clear()
        print("\n" + "═" * 60)
        print("SELECT MAP FILE".center(60))
        print("═" * 60)

        current_rel = current_dir.relative_to(maps_root)
        print(f"\n📁 Path: {current_rel}\n")

        items = []
        paths: List[Union[str, None]] = []

        if current_dir != maps_root:
            items.append("⬅️  Back to parent")
            paths.append("..")

        try:
            entries = sorted(current_dir.iterdir())
            for entry in entries:
                if entry.name.startswith((".", "_", "venv", "requirements")):
                    continue
                if entry.is_dir():
                    items.append(f"📁 {entry.name}/")
                    paths.append(entry.name)
                elif entry.suffix == ".txt":
                    items.append(f"📄 {entry.name}")
                    paths.append(entry.name)
        except PermissionError:
            print(UX["permission_denied"])
            continue

        if not items:
            print(UX["no_files_found"])
            continue

        items.append("❌ Exit")
        paths.append(None)

        idx = menu(items)

        if idx is None:
            return None

        selected = paths[idx]
        if selected is None:
            return None

        if selected == "..":
            current_dir = current_dir.parent
            continue

        path = current_dir / selected
        if path.is_dir():
            current_dir = path
            continue

        if path.is_file() and path.suffix == ".txt":
            return str(path)


def title() -> str:
    """Generates the ASCII title graphic for game screens.

    Returns:
        str: Centered multiline ASCII string.
    """
    ascii_art = r"""   ___  ___
 /'___\/\_ \                      __
/\ \__/\//\ \    __  __          /\_\    ___
\ \ ,__\ \ \ \  /\ \/\ \  _______\/\ \ /' _ `\
 \ \ \_/  \_\ \_\ \ \_\ \/\______\\ \ \/\ \/\ \
  \ \_\   /\____\\/`____ \/______/ \ \_\ \_\ \_\
   \/_/   \/____/ `/___/> \         \/_/\/_/\/_/
                     /\___/
                     \/__/                      """
    return ascii_art.center(100)


def wait_for_enter(message: Optional[str]) -> None:
    """Halts execution until the user presses the 'Enter' key.

    Args:
        message (str, optional): Custom override string to display.
    """
    if message is None:
        message = UX["press_enter"]
    input(message)


def welcome() -> None:
    """Displays the interactive title graphic for program launch."""
    clear()
    print()
    print(title(), end="\n" * 3)
    wait_for_enter(None)


def goodbye() -> str:
    """Exits the application gracefully displaying parting graphics."""
    clear()
    print("\n\n")
    print(title(), end="\n" * 3)
    print(UX["goodbye"], "\n")
    sys.exit(0)


def slice_str(
    str_list: List[str], max_char_line: int, max_lines: int
) -> List[str]:
    """Truncates a list of strings to fit column and height limits.

    Args:
        str_list (List[str]): The incoming unsanitized rows.
        max_char_line (int): Maximum characters per line.
        max_lines (int): Maximum allowed height.

    Returns:
        List[str]: Strings formatted into constrained boundaries.
    """
    str_list = str_list[:max_lines]
    new = [line for s in str_list for line in wrap(s, max_char_line)]
    return new


def offset_sequence(
        max_offset: Optional[int] = None) -> Generator[int, None, None]:
    """Generates an alternating sequence (e.g., 0, 1, -1, 2, -2).

    Args:
        max_offset (int, optional): Constrains loop upper boundary.

    Yields:
        int: Sequential alternating offset iterations.
    """
    yield 0
    offset = 1
    while max_offset is None or offset <= max_offset:
        yield offset
        yield -offset
        offset += 1
