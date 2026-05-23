from typing import Tuple, Dict, Generator
from itertools import count
import sys
import json


def import_texts(language: str) -> Tuple[Dict, Dict, Dict]:
    """
    Imports text from text json
    """
    file = f'{language}_texts.json'

    try:
        print('Loading texts...', end='')
        with open(file, 'r') as raw:
            texts = json.load(raw)
            print(' OK')
            return (texts['ux'], texts['status'], texts['error'])
    
    except FileNotFoundError as e:
        print(' FAIL')
        print(f'CRITICAL ERROR: {e}')
        sys.exit('Aborting launch...')


UX, STATUS, ERROR = import_texts('en')

path_id_generator = count(1)
