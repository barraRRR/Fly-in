.PHONY: install, run, debug, clean, lint, lint-strict

install:
		python3 -m venv venv
		venv/bin/pip install --upgrade pip
		venv/bin/pip install -r requirements.txt
		rm -rf maps
		rm -f maps.tar.gz
		venv/bin/python3 -m wget https://cdn.intra.42.fr/document/document/49269/maps.tar.gz
		tar -xvf maps.tar.gz
		rm -rf maps.tar.gz
		rm -f en.subject.pdf
		venv/bin/python3 -m wget -o en.subject.pdf https://cdn.intra.42.fr/pdf/pdf/204760/en.subject.pdf

run:
		./venv/bin/python3 fly_in.py

debug:
		venv/bin/python3 -m pdb fly_in.py

clean:
		rm -rf __pycache__
		rm -rf .pytest_cache
		rm -rf .mypy_cache
		rm output_file.txt

lint:
		venv/bin/flake8 . --exclude=venv && venv/bin/mypy . --exclude venv --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:
		venv/bin/flake8 . --exclude=venv && venv/bin/mypy . --exclude venv --strict