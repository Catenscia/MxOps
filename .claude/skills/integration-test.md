---
description: Run MxOps integration tests on chain-simulator
user-invocable: true
---

# Integration Test

Run MxOps integration tests on the MultiversX chain-simulator.

## Usage

- `/integration-test` - Run full integration test suite

## Steps

1. Start the chain-simulator
2. Run setup script
3. Execute integration tests
4. Stop the chain-simulator

## Commands

```bash
# Start chain-simulator (Docker must be running)
uv run mxops chain-simulator start

# Run setup
bash integration_tests/scripts/setup.sh chain-simulator

# Run tests
bash scripts/launch_integration_tests.sh chain-simulator

# Stop chain-simulator
uv run mxops chain-simulator stop
```

## Requirements

- **Docker** must be running
- Use `uv run mxops` for development version (not globally installed mxops)

## Notes

- The chain-simulator runs in Docker
- Setup script deploys necessary contracts and configures test environment
- Tests run against the local chain-simulator instance
- Always stop the simulator after testing to free resources
