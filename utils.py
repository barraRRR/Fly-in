from typing import Tuple, Dict
from itertools import count
import sys
import os
import json


def import_texts(language: str) -> Tuple[Dict, Dict, Dict, Dict]:
    """
    Imports text from text json
    """
    file = f'{language}_texts.json'

    try:
        print('Loading texts...', end='')
        with open(file, 'r') as raw:
            texts = json.load(raw)
            print(' OK')
            return (texts['ux'], texts['status'], texts["warning"], texts['error'])
    
    except FileNotFoundError as e:
        print(' FAIL')
        print(f'CRITICAL ERROR: {e}')
        sys.exit('Aborting launch...')


UX, STATUS, WARNING, ERROR = import_texts('en')
DELAY: int = 1
path_id_generator = count(1)


def clear() -> None:
    """
    Clear the terminal screen.
    Uses platform-specific commands (cls for Windows, clear for Unix-like systems).
    """
    os.system('cls' if os.name == 'nt' else 'clear')
