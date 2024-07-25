# Repository things

init: poetry-dev hooks env

poetry-dev:
	poetry install --with=dev --with=test

hooks:
	poetry run pre-commit install --hook-type pre-commit --hook-type commit-msg

# Codestyle things
static-check: style-check type-check

type-check:
	poetry run pyright

style-check:
	poetry run flake8 src --verbose

format:
	poetry run black .


# Testing things
test: test-pytest

test-pytest:
	poetry run pytest tests

check-all: style-check type-check test
