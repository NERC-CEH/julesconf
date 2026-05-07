_:
  @just lint typecheck test docs

# Format and lint the package using ruff, and lint the examples using marimo.
lint:
  ruff format
  ruff check --fix

# Check formatting and lint (for CI, doesn't modify files).
lint-check:
  ruff format --check
  ruff check

# Run the test suite using pytest.
test:
  pytest

# Run tests with coverage report.
test-cov:
  pytest --cov=dirconf --cov-report=term-missing --cov-fail-under=90

# Run static type checker.
typecheck:
  pyright

# Build the documentation.
docs:
  zensical build
