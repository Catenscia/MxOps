# Wrapping

This example will show you how to query and call external contracts.

We will use an eGLD wrapper on the devnet as the external contract. The plan is to execute the following actions:

- retrieve the token identifier of WEGLD
- Send eGLD to the contract to wrap them
- Send the WEGLD to the contract to retrieve the eGLD back

## Structure

We only need to create some `Scenes` so our folder structure we be as below:

```bash
.
├── mxops_scenes
└── wallets/
    └── devnet_user.pem
```

## Accounts and External Contract

We will define the external contract at the same time as the account. This way, we won't have to include it in every `Scene` we write. We will name this contract "egld_wrapper_shard_1".

```yaml
allowed_networks:
  - devnet

allowed_scenario:
  - "wrapping.*"

accounts:
  - account_id: user
    pem_path: ./wallets/devnet_user.pem

external_contracts:
  egld_wrapper_shard_1: erd1qqqqqqqqqqqqqpgqpv09kfzry5y4sj05udcngesat07umyj70n4sa2c0rp

```

## Scene

As we want to interact with wrapped eGLD, we will need to have its token identifier. The simplest way
is to make a query to the wrapper contract and save the token identifier in the `Scenario`.

```yaml
  - type: ContractQuery
    contract: egld_wrapper_shard_1
    endpoint: getWrappedEgldTokenId
    arguments: []
    results_types:
      - type: TokenIdentifier
    results_save_keys:
      - WrappedTokenIdentifier
```

We can then wrap some eGLD by calling the endpoint "wrapEgld". To be sure that everything went alright, we will check that the transaction
was successful, that the eGLD was sent to the contract and that we received wrapped eGLD in exchange.

```yaml
  - type: ContractCall
    sender: user
    contract: egld_wrapper_shard_1
    endpoint: wrapEgld
    value: 10000
    gas_limit: 3000000
    checks:
      - type: Success

      - type: Transfers
        condition: exact
        expected_transfers:
          - sender: "%user.address"
            receiver: "%egld_wrapper_shard_1.address"
            token_identifier: EGLD
            amount: 10000
          - sender: "%egld_wrapper_shard_1.address"
            receiver: "%user.address"
            token_identifier: "%egld_wrapper_shard_1.WrappedTokenIdentifier"
            amount: 10000
```

And lastly we can unwrap our WEGLD:

```yaml
  - type: ContractCall
    sender: user
    contract: egld_wrapper_shard_1
    endpoint: unwrapEgld
    gas_limit: 3000000
    esdt_transfers:
      - token_identifier: "%egld_wrapper_shard_1.WrappedTokenIdentifier"
        amount: 10000
        nonce: 0
    checks:
      - type: Success

      - type: Transfers
        condition: exact
        expected_transfers:
          - sender: "%user.address"
            receiver: "%egld_wrapper_shard_1.address"
            token_identifier: "%egld_wrapper_shard_1.WrappedTokenIdentifier"
            amount: 10000
          - sender: "%egld_wrapper_shard_1.address"
            receiver: "%user.address"
            token_identifier: EGLD
            amount: 10000
```

We can put these three `Steps` in a new file at `mxops_scenes/01_scene.yaml` and here is the complete content:

```yaml
allowed_networks:
  - localnet
  - testnet
  - devnet

allowed_scenario:
  - "wrapping.*"

steps:
  
  - type: ContractQuery
    contract: egld_wrapper_shard_1
    endpoint: getWrappedEgldTokenId
    arguments: []
    results_types:
      - type: TokenIdentifier
    results_save_keys:
      - WrappedTokenIdentifier

  - type: ContractCall
    sender: user
    contract: egld_wrapper_shard_1
    endpoint: wrapEgld
    value: 10000
    gas_limit: 3000000
    checks:
      - type: Success

      - type: Transfers
        condition: exact
        expected_transfers:
          - sender: "%user.address"
            receiver: "%egld_wrapper_shard_1.address"
            token_identifier: EGLD
            amount: 10000
          - sender: "%egld_wrapper_shard_1.address"
            receiver: "%user.address"
            token_identifier: "%egld_wrapper_shard_1.WrappedTokenIdentifier"
            amount: 10000

  - type: ContractCall
    sender: user
    contract: egld_wrapper_shard_1
    endpoint: unwrapEgld
    gas_limit: 3000000
    esdt_transfers:
      - token_identifier: "%egld_wrapper_shard_1.WrappedTokenIdentifier"
        amount: 10000
        nonce: 0
    checks:
      - type: Success

      - type: Transfers
        condition: exact
        expected_transfers:
          - sender: "%user.address"
            receiver: "%egld_wrapper_shard_1.address"
            token_identifier: "%egld_wrapper_shard_1.WrappedTokenIdentifier"
            amount: 10000
          - sender: "%egld_wrapper_shard_1.address"
            receiver: "%user.address"
            token_identifier: EGLD
            amount: 10000
```

### Execution

To execute our example on the devnet, we can write this command:

```bash
mxops execute \
        -n devnet \
        -s wrapping_example \
        mxops_scenes/accounts/devnet_accounts.yaml \
        mxops_scenes/01_scene.yaml
```

This will give you an output like this:

```bash
MxOps  Copyright (C) 2023  Catenscia
This program comes with ABSOLUTELY NO WARRANTY
[2023-02-24 19:00:16,832 data INFO] Scenario wrapping_example created for network devnet [data:287 in create_scenario]
[2023-02-24 19:00:16,833 scene INFO] Executing scene mxops_scenes/accounts/devnet_accounts.yaml [scene:69 in execute_scene]
[2023-02-24 19:00:16,928 scene INFO] Executing scene mxops_scenes/01_scene.yaml [scene:69 in execute_scene]
[2023-02-24 19:00:16,931 steps INFO] Query on getWrappedEgldTokenId for egld_wrapper_shard_1 [steps:211 in execute]
[2023-02-24 19:00:17,040 steps INFO] Saving Query results as contract data [steps:223 in execute]
[2023-02-24 19:00:17,040 steps INFO] Query successful [steps:231 in execute]
[2023-02-24 19:00:17,044 steps INFO] Calling wrapEgld for egld_wrapper_shard_1 [steps:173 in execute]
[2023-02-24 19:00:22,249 steps INFO] Call successful: https://devnet-explorer.multiversx.com/transactions/ecc39ee4dc17cacc70fddc1c022a95c1d74644db0227a9d391a29d6d4e3346fe [steps:188 in execute]
[2023-02-24 19:00:22,250 steps INFO] Calling unwrapEgld for egld_wrapper_shard_1 [steps:173 in execute]
[2023-02-24 19:00:27,445 steps INFO] Call successful: https://devnet-explorer.multiversx.com/transactions/05eab380d05907f4f49dfe846fe09117a07789025eab8b5a82eaef0c69ae975f [steps:188 in execute]
```
