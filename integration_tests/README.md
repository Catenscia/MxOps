# Integration Tests

This folder contains the integration tests of `MxOps`. These tests are meant to be run on devnet or chain-simulator to make sure that `MxOps` functionnalities are operationnal on live nets.

Some tests are only executable on the chain-simulator, some only on devnet, the rest on both. The tests are designed to be run directly from the root of this repository.

For develop PRs, we recommend to only run the integration tests on the chain-simulator, as interacting with the devnet takes a lot of times and it adds very little test coverage.

## Chain simulator

```bash
mxops chain-simulator start
bash integration_tests/scripts/setup.sh chain-simulator
bash scripts/launch_integration_tests.sh chain-simulator
```

After everyting is over, you can inspect the local explorer for the chain simulator if you wish, otherwise, shutdown the chain-simulator

```bash
mxops chain-simulator stop
```

## Devnet

For devnet, the wallets should already have some funds. If they don't, run the faucet command:

```bash
bash integration_tests/scripts/setup.sh devnet
```

and then launch the integration tests

```bash
bash scripts/launch_integration_tests.sh devnet
```

