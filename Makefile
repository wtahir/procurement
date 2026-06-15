.PHONY: install test lint format run-api

install:
	. .venv/bin/activate && pip install --upgrade pip && pip install -r requirements-dev.txt

test:
	. .venv/bin/activate && pytest

lint:
	. .venv/bin/activate && ruff check . --line-length 100 --target-version py312 --select E,F,I,UP,B && mypy --config-file mypy.ini apps packages tests

format:
	. .venv/bin/activate && ruff check . --fix --line-length 100 --target-version py312 --select E,F,I,UP,B

run-api:
	. .venv/bin/activate && uvicorn apps.api.main:app --reload
