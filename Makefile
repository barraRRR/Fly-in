.PHONY: install, run, debug, clean, lint

install:
		python3 -m venv venv
		venv/bin/pip install --upgrade pip
		venv/bin/pip install -r requirements.txt
		rm -rf maps
		venv/bin/python3 -m wget https://cdn.intra.42.fr/document/document/49269/maps.tar.gz
		tar -xvf maps.tar.gz
		rm -rf maps.tar.gz

run:
		. source venv/bin/avtivate & python3 fly_in.py

debug:
		pytest test_fly_in.py

clean:
		rm -rf __pycache__
		rm -rf .pytest_cache
		rm -rf .mypy_cache

lint:
		flake8 . --exclude=venv,test_fly_in.py && mypy . --exclude venv --exclude test_fly_in.py --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs