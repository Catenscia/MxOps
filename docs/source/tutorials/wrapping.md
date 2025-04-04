# Wrapping

This example relies on the MxOps integration test called [wrapping](https://github.com/Catenscia/MxOps/tree/main/integration_tests/wrapping). It can exclusively be executed on the devnet.

This example showcase the following topics:

- queries
- calls
- checks

## Context

This example is pretty simple, it does the following on the devnet:

1. Make a query to get the WEGLD identifier from the devnet egld wrapper contract.
2. Send EGLD to the contract to wrap them while checking that the transfers are correct (EGLD is received by the contract and WEGLD is received by the caller)
3. Send WEGLD to the contract to unwrap them while checking that the transfers are correct (WEGLD is received by the contract and EGLD is received by the caller)

That's it! This example is pretty light weight so you shouldn't have too much trouble understanding it while going through the [source code](https://github.com/Catenscia/MxOps/tree/main/integration_tests/wrapping).
