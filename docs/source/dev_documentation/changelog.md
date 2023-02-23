# ChangeLog

## Unreleased

### Added

- Check classes for `CallStep`
- External contract support for contract calls and queries (including results save)
- CI and script for bandit, flake8 and pylint
- CI for pytest tests
- CI for python package build
- CI for package publication on PYPI

### Changed

- 🚨 BREAKING CHANGE 🚨 `contract_id` attribute renamed to `contract` for calls and queries
- 🚨 BREAKING CHANGE 🚨 Refactor check_for_errors attribute to be more general (allow more checks in the future)

### Removed

- None

## 0.1.1 - 2023-01-24

### Added

- Readthedocs yaml configuration file to fix compilation
- Full user tutorial in the sphinx documentation

### Changed

- None

### Removed

- None

## 0.1.0 - 2023-01-23

First version of MxOps.
