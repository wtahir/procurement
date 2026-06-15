.PHONY: install test lint format run-api

install:
	. .venv/bin/activate && pip install --upgrade pip && pip install -e .[dev]

test:
	. .venv/bin/activate && pytest

lint:
	. .venv/bin/activate && ruff check . && mypy apps packages tests

format:
	. .venv/bin/activate && ruff check . --fix

run-api:
	. .venv/bin/activate && uvicorn apps.api.main:app --reload
