.PHONY: install

install:
		python3 -m venv venv
		pip install --upgrade pip
		pip install -r requirements.txt

run:
		. source venv/bin/avtivate & python3 fly_in.py

debug:
		pytest test_fly_in.py

clean:
		rm -rf __pychache__
		rm -rf .pytest_cache
		rm -rf .mypy_cache

lint:
		flake8 . && mypy . --warn-return-any --warn-unused-ignores--ignore-missing-imports--disallow-untyped-defs --check-untyped-defs