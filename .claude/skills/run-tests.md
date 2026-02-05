---
description: Run MxOps unit tests with pytest and coverage
user-invocable: true
---

# Run Tests

Run MxOps unit tests with pytest and coverage.

## Usage

- `/run-tests` - Run all unit tests
- `/run-tests tests/test_smart_values.py` - Run specific test file
- `/run-tests -k "test_name"` - Run tests matching pattern

## Commands

For all tests:
```bash
bash scripts/launch_unit_tests.sh
```

For specific tests or patterns:
```bash
uv run coverage run -m pytest tests/<path> --color=yes -vv
```

## Notes

- Tests use pytest with coverage reporting
- Coverage report is generated after test run
- Use `uv run` prefix if running outside the virtual environment
