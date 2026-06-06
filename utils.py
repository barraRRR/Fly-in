from typing import Tuple, Dict, List
from itertools import count
from pathlib import Path
from simple_term_menu import TerminalMenu
from textwrap import wrap
import sys
import os
import json


def import_texts(language: str) -> Tuple[Dict, Dict, Dict, Dict]:
    """Imports application texts safely from a targeted JSON file based
    on the selected language.

    Args:
        language (str): Locale code (e.g., 'en') defining which JSON
            file to fetch.

    Returns:
        Tuple[Dict, Dict, Dict, Dict]: Grouped dictionaries representing
            UX, status, warnings, and errors.
    """
    file = f'{language}_texts.json'

    try:
        print('Loading texts...', end='')
        with open(file, 'r') as raw:
            texts = json.load(raw)
            print(' OK')
            return (
                texts['ux'], texts['status'], texts["warning"], texts['error']
            )

    except FileNotFoundError as e:
        print(' FAIL')
        print(f'CRITICAL ERROR: {e}')
        sys.exit('Aborting launch...')


UX, STATUS, WARNING, ERROR = import_texts('en')
UX_MAX: int = 500
UX_STD: int = 100
DELAY: float = 0.5
FAST: float = 0.1
DIRECT: float = 0.0
PACE = DELAY
path_id_generator = count(1)
drone_helices = count(1)


def clear() -> None:
    """Clears the console or terminal screen cleanly.
    
    Checks the underlying OS in order to dispatch platform-specific commands ('cls' or 'clear').
    """
    os.system('cls' if os.name == 'nt' else 'clear')


def menu(items: List[str]) -> int:
    """Deploys an interactive terminal UI menu containing selectable options.

    Args:
        items (List[str]): List of textual options to display sequentially.

    Returns:
        int: The index corresponding to the user's selected string.
            Returns -1 if cancelled.
    """
    menu_obj = TerminalMenu(
        items,
        title="Use ↑ ↓ arrows to navigate, ENTER to select",
        menu_cursor="➜ ",
        menu_cursor_style=("fg_cyan", "bold"),
        show_search_hint=False
    )
    idx = menu_obj.show()
    return idx if idx is not None else -1


def select_map_file() -> str:
    """Invokes a visual directory traversal tool enabling users to pick
    a `.txt` file map.

    Returns:
        str: The fully qualified or relative file path pointing to the
            selected map.
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
        paths = []

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
        
        if idx is None or paths[idx] is None:
            return None

        selected = paths[idx]

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
    """Generates the ASCII title graphic for the start or end game screens.

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


def wait_for_enter(message: str = None) -> None:
    """Halts code execution until the user manually strikes the 'Enter' key.

    Args:
        message (str, optional): Custom override string to display before
            halting. Defaults to None.
    """
    if message is None:
        message = UX["press_enter"]
    input(message)


def welcome() -> str:
    """Displays the interactive title graphic explicitly dedicated for
    program launch.
    """
    clear()
    print()
    print(title(), end="\n" * 3)
    wait_for_enter()


def goodbye() -> str:
    """Exits the application gracefully displaying parting ASCII graphics
    and halting the process.
    """
    clear()
    print("\n\n")
    print(title(), end="\n" * 3)
    print(UX["goodbye"])
    sys.exit(0)


def slice_str(str_list: List[str], max_char_line: int, max_lines: int) -> List[str]:
    """Splits and truncates a list of strings strictly conforming to
    column-width/max-height formatting.

    Args:
        str_list (List[str]): The incoming unsanitized rows.
        max_char_line (int): Permitted character boundary per line row.
        max_lines (int): Terminal allowed bounding limit height for
            the content.

    Returns:
        List[str]: Refactored strings formatted into safely constrained
            boundaries.
    """
    str_list = str_list[:max_lines]
    new = [line for s in str_list for line in wrap(s, max_char_line)]
    return new


def offset_sequence(max_offset=None):
    """Generates an alternating infinite or bound numerical sequence
    (e.g., 0, 1, -1, 2, -2).

    Args:
        max_offset (int, optional): Constrains loop upper magnitude
            boundary. Defaults to None.

    Yields:
        int: Sequential incremental/decremental offset iterations.
    """
    yield 0
    offset = 1
    while max_offset is None or offset <= max_offset:
        yield offset
        yield -offset
        offset += 1