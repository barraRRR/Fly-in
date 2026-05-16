.PHONY: install

install:
		python3 -m venv venv
		pip install --upgrade pip
		pip install -r requirements.txt

run:
		. source venv/bin/avtivate &