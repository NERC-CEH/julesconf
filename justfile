_:
  @just lint typecheck test

# Format and lint the package using ruff, and lint the examples using marimo.
lint:
  ruff format
  ruff check --fix
  marimo check examples/

# Check formatting and lint (for CI, doesn't modify files).
lint-check:
  ruff format --check
  ruff check
  marimo check examples/

# Run the test suite using pytest.
test:
  pytest

# Run tests with coverage report.
test-cov:
  pytest --cov=julesconf --cov-report=term-missing --cov-fail-under=90

# Run static type checker.
typecheck:
  pyright

# Build the documentation.
docs:
  cd examples/ && marimo-md-export 101.py ../docs/tutorials/editing-namelists.md
  ruff format examples/  # override marimo's annoying reformatting
  zensical build
