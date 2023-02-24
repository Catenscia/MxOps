# Overview

MxOps is a python package created to automate MultiversX smart contracts deployments, calls and queries.
Inspired from DevOps tools, it aims to ease and make reproducible any set of these interactions with smart-contracts.

MxOps aims to be useful in these situations:

- deployment automation
- on-chain integration tests
- contract interaction automation

## User Flow

MxOps works with yaml files, called `Scenes`. This allows version control on MxOps executions.
Each `Scene` contains any given number of `steps`. Each `step` is an interaction with a contract: be it a deployment, a call, an upgrade or a query.

To execute `Scenes`, the user chooses a network (mainnet, devnet, testnet or localnet) and a `Scenario`.
`Scenario` are an environment in which the results of the every `step` execution will be stored locally on your computer. This allows to execute identical `Scenes` on different contracts in the **same** network and it is also essential to use these results at a later time (for example to upgrade a contract).

## Scene Example

Below is an example scene where a user want to deploy a contract and then call this contract to issue a new token.

Heads to the {doc}`scenes` section for detailed explanation.

```yaml
allowed_networks:
  - DEV
  - MAIN

allowed_scenario:
  - "deploy_and_mint"

accounts:
  - account_name: owner
    pem_path: ./wallets/my_devnet_wallet.pem

steps:
  - type: ContractDeploy
    sender: owner
    wasm_path: "./contracts/my_contract.wasm"
    contract_id: "abc-esdt-minter"
    gas_limit: 50000000
    arguments:
      - 100
    upgradeable: True
    readable: False
    payable: False
    payable_by_sc: True

  - type: ContractCall
    sender: owner
    contract: "abc-esdt-minter"
    endpoint: issueToken
    gas_limit: 100000000
    value: "&BASE_ISSUING_COST"
    arguments:
      - ABC
      - ABC
      - 3
```

## Next Step

You are now ready to heads up to the {doc}`getting_started` section!
