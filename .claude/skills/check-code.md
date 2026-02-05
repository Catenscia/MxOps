---
description: Run all MxOps code quality checks required before PR
user-invocable: true
---

# Check Code

Run all MxOps code quality checks required before PR.

## Tools

1. **Bandit** - Security analysis (must have no issues)
2. **Flake8** - Style checking (must pass, max-line-length=88)
3. **Ruff** - Format + lint (must pass)
4. **Pylint** - Code analysis (score >= 9.5)

## Usage

- `/check-code` - Run all checks
- `/check-code --fix` - Auto-fix formatting issues first, then run checks

## Commands

Run all checks:
```bash
bash scripts/check_python_code.sh
```

Auto-fix and check:
```bash
ruff format mxops && ruff check mxops --fix
bash scripts/check_python_code.sh
```

Or run individual tools:
```bash
# Security check
bandit -r mxops

# Style check
flake8 mxops tests integration_tests examples

# Format and lint
ruff format mxops
ruff check mxops

# Code analysis
pylint mxops
```

## Notes

- All checks must pass before submitting a PR
- Ruff can auto-fix many issues with `ruff format` and `ruff check --fix`
- Pylint score must be >= 9.5
