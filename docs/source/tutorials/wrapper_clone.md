# Wrapper Clone

This example relies on the MxOps integration test called [wrapper clone](https://github.com/Catenscia/MxOps/tree/main/integration_tests/wrapper_clone). It can exclusively be executed on the chain-simulator.

This example showcase the following topics:

- chain-simulator
- account cloning
- queries
- calls
- checks

## Context

This example is pretty simple, it does the following:

1. Clone the egld wrapper contract from mainnet to chain-simulator
2. Make a query to get the WEGLD identifier from the cloned contract
3. Send EGLD to the contract to wrap them while checking that the transfers are correct (EGLD is received by the contract and WEGLD is received by the caller)
4. Send WEGLD to the contract to unwrap them while checking that the transfers are correct (WEGLD is received by the contract and EGLD is received by the caller)

That's it! This example is pretty light weight so you shouldn't have too much trouble understanding it while going through the [source code](https://github.com/Catenscia/MxOps/tree/main/integration_tests/wrapper_clone).
