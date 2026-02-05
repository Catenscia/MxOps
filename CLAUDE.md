# MxOps Development Guide

MxOps is a Python automation tool for MultiversX blockchain. Users write YAML scene files that describe steps (contract deployments, calls, queries, token management) which MxOps executes.

## Quick Reference

### Essential Commands
```bash
# Install dev dependencies
uv sync --group dev

# Run ALL checks before PR (required)
bash scripts/local_checks.sh

# Run unit tests only
bash scripts/launch_unit_tests.sh

# Run integration tests (chain-simulator)
uv run mxops chain-simulator start
bash integration_tests/scripts/setup.sh chain-simulator
bash scripts/launch_integration_tests.sh chain-simulator
uv run mxops chain-simulator stop
```

### Testing Development Changes
```bash
# Use development version (NOT globally installed mxops)
uv run mxops <command>
# or
python -m mxops <command>
```

### Code Quality (all must pass for PR)
- **Bandit**: `bandit -r mxops` - no security issues
- **Flake8**: `flake8 mxops tests integration_tests examples` - max-line-length=88
- **Ruff**: `ruff format mxops && ruff check mxops` - format + lint
- **Pylint**: `pylint mxops` - score >= 9.5

## Architecture

### Core Flow
```text
YAML Scene -> Steps -> Transactions/Queries -> MultiversX Network
```

### Key Directories
| Directory | Purpose |
|-----------|---------|
| `mxops/execution/steps/` | All step implementations (28 types) |
| `mxops/smart_values/` | Dynamic value resolution (`%`, `$`, `&`, `=` syntax) |
| `mxops/data/` | ScenarioData persistence per network+scenario |
| `mxops/cli/` | CLI commands (execute, data, config, chain-simulator) |
| `tests/` | Unit tests (pytest) |
| `integration_tests/` | Chain-simulator/devnet integration tests |

### All Step Types (28)
**Contracts**: `ContractDeploy`, `ContractUpgrade`, `ContractCall`, `ContractQuery`, `FileFuzzer`
**Transfers**: `Transfer`
**Tokens**: `FungibleIssue`, `NonFungibleIssue`, `SemiFungibleIssue`, `MetaIssue`, `FungibleMint`, `NonFungibleMint`, `ManageFungibleTokenRoles`, `ManageNonFungibleTokenRoles`, `ManageSemiFungibleTokenRoles`, `ManageMetaTokenRoles`
**Setup**: `GenerateWallets`, `ChainSimulatorFaucet`, `R3D4Faucet`, `AccountClone`
**Control**: `Loop`, `Scene`, `SetVars`, `SetSeed`, `Assert`, `Wait`, `Log`, `Python`

### Smart Values Syntax
| Symbol | Source | Example |
|--------|--------|---------|
| `%` | Scenario data | `%contract_id.address`, `%saved_value` |
| `$` | Environment var | `$MY_ENV_VAR` |
| `&` | Config file | `&PROXY` |
| `=` | Formula | `=10**18`, `=randint(1,5)` |

**Formula functions**: `int`, `str`, `float`, `rand`, `randint`, `choice`, `ceil`, `len`

**Composition**: `%{${OWNER}_token.identifier}`, `={%{amount_1} + %{amount_2}}`

## Adding New Steps

1. Create dataclass in `mxops/execution/steps/<module>.py`
2. Inherit from `Step` (non-tx) or `TransactionStep` (tx)
3. Implement `_execute()` or `build_unsigned_transaction()`
4. Export in `mxops/execution/steps/__init__.py`
5. Add tests in `tests/`

Pattern:
```python
@dataclass(kw_only=True)
class MyStep(TransactionStep):
    my_param: SmartStr
    optional_param: SmartInt | None = None

    def build_unsigned_transaction(self) -> Transaction:
        param = self.my_param.get_evaluated_value()
        ...
```

## Branch/Commit Conventions

- **Branches**: `feature/<name>`, `fix/<name>`, `refactor/<name>`, `docs/<name>`, `test/<name>`, `breaking/<name>`
- **Commits**: Conventional Commits format (automated versioning depends on this)
- **PRs target**: `develop` branch

## Gotchas

1. **Smart values must be quoted in YAML**: Use `"%var"` not `%var`
2. **Step type suffix optional**: `ContractCall` and `ContractCallStep` both work
3. **Formula results are typed**: `=10**18` returns int, use `=str(...)` if string needed
4. **Scenario isolation**: Each network+scenario combo has separate persisted data
5. **ABI recommended**: Always provide ABI for automatic argument encoding/decoding
