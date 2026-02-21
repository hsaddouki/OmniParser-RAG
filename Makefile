.PHONY: check fix lint format typecheck test install install-hooks

## install — install package + dev dependencies
install:
	python -m pip install -e ".[dev]"

## check — run all checks without modifying files
check: lint typecheck test

## lint — ruff check only (no fixes)
lint:
	ruff check src/ tests/

## format-check — verify formatting without writing changes
format-check:
	ruff format --check src/ tests/

## fix — auto-fix linting issues + reformat
fix:
	ruff check --fix src/ tests/
	ruff format src/ tests/

## typecheck — run mypy
typecheck:
	mypy src/

## test — run pytest
test:
	pytest tests/

## install-hooks — install pre-commit hooks
install-hooks:
	python -m pre_commit install
