# Enhanced First Scene

In the section we will modify our initial `Scene` that was made to deploy and interact with the ping-pong contract.

## Account Scenes

The improvement here will take advantage of the fact that when launching `MxOps`, we can specify several files and/or folders with `Scenes`.

We will define the accounts in separate files per network type. Let's start by creating folder `mxops_scenes` with a sub_folder `accounts`.

We will write the `Scene`  `mxops_scenes/accounts/devnet.yaml` with no step at all, just the account definition:

```yaml
allowed_networks:
    - devnet

allowed_scenario:
    - ".*"

accounts:
  - account_name: owner
    pem_path: ./wallets/my_devnet_wallet.pem
```

To avoid any mistake, we recommend (not only for `MxOps` but in general) dedicating wallets to a single network: each wallet should interact only with a single network. This makes it harder mix-up networks.

For example if you wanted to execute this tutorial on the local net, you could create the `mxops_scenes/accounts/local.yaml`:

```yaml
allowed_networks:
    - localnet

allowed_scenario:
    - ".*"

accounts:
  - account_name: owner
    pem_path: ./wallets/bob.pem  # one of the default public account with funds on the localnet
```

Two details to notice:

- a regex has been used for the allowed `Scenarios`: we want to allow all `Scenarios` as we are just specifying the account.
- the wallets my_devnet_wallet and bob have been defined with the same name: we only have to refer to the account name "owner" in the scenes we will write later on.

## Deploy Scene

The deployment will be written in a separate `Scene` so that we can ping and pong the contract later on without having to deploy a new contract each time.

Create the new file `mxops_scenes/deploy.yaml`:

```yaml
allowed_networks:
    - devnet
    - localnet

allowed_scenario:
    - mxops_tutorial_enhanced_first_scene

steps:

  - type: ContractDeploy
    sender: owner
    wasm_path: "./contract/ping-pong/output/ping-pong.wasm"
    contract_id: "egld-ping-pong"
    gas_limit: 40000000
    arguments:
      - "$PING_PONG_AMOUNT:int"
      - "$PONG_WAIT_TIME:int"
    upgradeable: true
    readable: false
    payable: false
    payable_by_sc: true
```

Three important changes:

- The devnet and the localnet have been allowed to execute this `Scene`
- We changed the `Scenario` name to "mxops_tutorial_enhanced_first_scene"
- Instead of writing the ping amount and the pong wait time directly in the scene, we will pull them from environment variables.

## PingAmount and Query

We can now write the final `Scene`of this tutorial. And for this occasion let's introduce a new component: The `ContractQuery` `Step`. This tells `Mxops` to query the view of a contract and optionally you can save the results and/or print it.

In our situation let's say that we forgot what is the ping amount we need to send to our contract. We could look at the deploy transaction and look at the supplied arguments but that is not convenient. Instead we will query the ping amount directly from the deployed contract and save this value for when we want to ping.

Such `Step` would look like this:

```yaml
  - type: ContractQuery
    contract: "egld-ping-pong"
    endpoint: getPingAmount
    expected_results:
      - save_key: PingAmount
        result_type: number
```

This tells `MxOps` to save (in the current `Scenario`) the value from the query result and to attach it to the contract "egld-ping-pong" under the key name "PingAmount".

We can reuse this value during the ping `Step`:

```yaml
  - type: ContractCall
    sender: owner
    contract: "egld-ping-pong"
    endpoint: ping
    gas_limit: 3000000
    value: "%egld-ping-pong.PingAmount"
```

This 'save&reuse' workflow allows you to make complex and dynamic `Scenes`: it can save you a ton of time in situations like complex and interdependent multi-deployment.

## Transfer Check

MxOps checks by default that a transaction is successful. In our case, we would also like to check that the eGLD transfer was correctly executed during the ping and pong transaction. This is done by specifying a `TransfersCheck` in the `ContractCall` `Step`:

```yaml
  - type: ContractCall
    sender: owner
    contract: "egld-ping-pong"
    endpoint: ping
    gas_limit: 3000000
    value: "%egld-ping-pong.PingAmount"
    checks:
      - type: Success

      - type: Transfers
        condition: exact
        expected_transfers:
          - sender: "[owner]"
            receiver: "%egld-ping-pong.address"
            token_identifier: EGLD
            amount: "%egld-ping-pong.PingAmount"
```

We take advantages of the variable format of MxOps to specify the value for the transfer. The above check tells MxOps that the transaction should contain only one transfer, and that it should be an eGLD transfer of `PingAmount` token from the user `owner` to the `egld-ping-pong` contract.

```{warning}
By default if checks are not specified by the user, MxOps will by default run a `SuccessCheck` on each transaction. However if you are using the `checks` keyword, don't forget to add the `SuccessCheck` if you need it!
```

But let's finish our `Scene` named `mxops_scenes/ping_pong.yaml` by adding the pong `Step`:

```yaml
allowed_networks:
    - devnet
    - localnet

allowed_scenario:
    - mxops_tutorial_enhanced_first_scene

steps:

  - type: ContractQuery
    contract: "egld-ping-pong"
    endpoint: getPingAmount
    expected_results:
      - save_key: PingAmount
        result_type: number

  - type: ContractCall
    sender: owner
    contract: "egld-ping-pong"
    endpoint: ping
    gas_limit: 3000000
    value: "%egld-ping-pong.PingAmount"

  - type: ContractCall
    sender: owner
    contract: "egld-ping-pong"
    endpoint: pong
    gas_limit: 3000000

```

Your folders structure should now look like this:

```text
mxops_tutorial
├── contract
│   ├── ping-pong
│   │   ├── output
│   │   │   ├── ping-pong.abi.json
│   │   │   └── ping-pong.wasm
│   │   ...
│   ...
├── mxops_scenes
│   ├── accounts
│   │   ├── devnet.yaml
│   │   └── local.yaml
│   ├── deploy.yaml
│   ├── ping-pong.yaml
└── wallets
    └── my_devnet_wallet.pem
```

## Execution

To deploy the contract on the devnet:

```bash
export PING_PONG_AMOUNT=1000000000000000000
export PONG_WAIT_TIME=1

mxops execute \
        -n devnet \
        -s mxops_tutorial_enhanced_first_scene \
        mxops_scenes/accounts/devnet.yaml \
        mxops_scenes/deploy.yaml
```

This will give you an output like this:

```bash
MxOps  Copyright (C) 2023  Catenscia
This program comes with ABSOLUTELY NO WARRANTY
[2023-02-24 07:21:10,414 data INFO] Scenario mxops_tutorial_enhanced_first_scene created for network devnet [data:287 in create_scenario]
[2023-02-24 07:21:10,414 scene INFO] Executing scene mxops_scenes/accounts/devnet.yaml [scene:69 in execute_scene]
[2023-02-24 07:21:10,518 scene INFO] Executing scene mxops_scenes/deploy.yaml [scene:69 in execute_scene]
[2023-02-24 07:21:10,521 steps INFO] Deploying contract egld-ping-pong [steps:100 in execute]
[2023-02-24 07:21:15,819 steps INFO] Deploy successful on erd1qqqqqqqqqqqqqpgqv2qu073e8vfv82ce2qt4dtcj4dqpga6rplcqvm6swg
tx hash: https://devnet-explorer.multiversx.com/transactions/b0b7c059f44793c03c535f17563dcc349e25972a1ccded6ac812a8c2cd9056c9 [steps:120 in execute]
```

To ping and pong the contract, we can use this:

```bash
mxops execute \
        -n devnet \
        -s mxops_tutorial_enhanced_first_scene \
        mxops_scenes/accounts/devnet.yaml \
        mxops_scenes/ping_pong.yaml
```

```bash
MxOps  Copyright (C) 2023  Catenscia
This program comes with ABSOLUTELY NO WARRANTY
[2023-02-24 07:21:24,667 data INFO] Scenario mxops_tutorial_enhanced_first_scene loaded for network devnet [data:262 in load_scenario]
[2023-02-24 07:21:24,667 scene INFO] Executing scene mxops_scenes/accounts/devnet.yaml [scene:69 in execute_scene]
[2023-02-24 07:21:24,823 scene INFO] Executing scene mxops_scenes/ping_pong.yaml [scene:69 in execute_scene]
[2023-02-24 07:21:24,826 steps INFO] Query on getPingAmount for egld-ping-pong [steps:211 in execute]
[2023-02-24 07:21:25,029 steps INFO] Saving Query results as contract data [steps:223 in execute]
[2023-02-24 07:21:25,029 steps INFO] Query successful [steps:231 in execute]
[2023-02-24 07:21:25,030 steps INFO] Calling ping for egld-ping-pong [steps:173 in execute]
[2023-02-24 07:21:35,308 steps INFO] Call successful: https://devnet-explorer.multiversx.com/transactions/bdbc4773fbe05aa8f86f2bbc2d09db26eb50dc1fe4276754acbe17ba106ee65c [steps:188 in execute]
[2023-02-24 07:21:35,308 steps INFO] Calling pong for egld-ping-pong [steps:173 in execute]
[2023-02-24 07:21:40,576 steps INFO] Call successful: https://devnet-explorer.multiversx.com/transactions/95003df0306888d0fb0606f7e6121028b9ac389f9e38b7ee68783fc0e2919e33 [steps:188 in execute]
```

You can notice the extra query `Step` in the logs compared to the first version of this tutorial.

You can now ping and pong the contract again, without making a new deployment each time.

## Data

Let's take a look at the data of the current `Scenario`:

```bash
mxops data get -n devnet -s mxops_tutorial_enhanced_first_scene
```

```bash
MxOps  Copyright (C) 2023  Catenscia
This program comes with ABSOLUTELY NO WARRANTY
[2023-02-24 17:39:46,283 data INFO] Scenario mxops_tutorial_enhanced_first_scene loaded for network devnet [data:262 in load_scenario]
{
    "name": "mxops_tutorial_enhanced_first_scene",
    "network": "devnet",
    "creation_time": 1677219670,
    "last_update_time": 1677219685,
    "contracts_data": {
        "egld-ping-pong": {
            "contract_id": "egld-ping-pong",
            "address": "erd1qqqqqqqqqqqqqpgqv2qu073e8vfv82ce2qt4dtcj4dqpga6rplcqvm6swg",
            "saved_values": {
                "PingAmount": 1000000000000000000
            },
            "wasm_hash": "1383133d22b8be01c4dc6dfda448dbf0b70ba1acb348a50dd3224b9c8bb21757",
            "deploy_time": 1677219672,
            "last_upgrade_time": 1677219672,
            "is_external": false
        }
    }
}
```

You can notice the "PingAmount" value has indeed been saved under the contract "egld-ping-pong".

Ladies and Gentlemen, it is now time to wrap things up and go towards the 👉 {doc}`conclusion of this tutorial<conclusion>` 🏁
