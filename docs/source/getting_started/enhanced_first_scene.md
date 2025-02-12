# Enhanced First Scene

In the section we will modify our initial `Scene` that was made to deploy and interact with the ping-pong contract.

## Account Scenes

The improvement here will take advantage of the fact that when launching MxOps, we can specify several `Scenes` to be executed sequentially or even entire folders with `Scenes`.

We will define the accounts in separate files per network type. Let's start by creating a folder `mxops_scenes` with a sub_folder `accounts`.

We will write the `Scene`  `mxops_scenes/accounts/devnet.yaml` with no step at all, just the devnet accounts definition:

```yaml
allowed_networks:
    - devnet

accounts:
  - account_name: owner
    pem_path: ./wallets/my_devnet_wallet.pem
```

```{note}
To avoid harmful mistakes, we recommend (not only for MxOps but in general) dedicating wallets to a single network: each wallet should interact with one and only one network. This makes it harder to mix-up networks and losing funds.
```

For example if you also wanted to execute this tutorial on a localnet, you could create the following `Scene` `mxops_scenes/accounts/local.yaml`:

```yaml
allowed_networks:
    - localnet

accounts:
  - account_name: owner
    pem_path: ./wallets/bob.pem  # one of the default public account with funds on the localnet
```

One detail to notice:
The wallets my_devnet_wallet.pem and bob.pem have been defined with the same `account_name`: in later `Scenes`, we only have to refer to the `account_name` "owner" and it will work both the `devnet` and the `localnet`.

## Deploy Scene

The deployment will be written in a separate `Scene` so that we can ping and pong the contract later on without having to deploy a new contract each time.

Create the new file `mxops_scenes/01_deploy.yaml`:

```yaml
steps:

  - type: ContractDeploy
    sender: owner
    wasm_path: "./contract/ping-pong/output/ping-pong.wasm"
    abi_path: "./contract/ping-pong/output/ping-pong.abi.json"
    contract_id: "egld-ping-pong"
    gas_limit: 40000000
    arguments:
      - "$PING_PONG_AMOUNT"
      - "$PONG_WAIT_TIME"
    upgradeable: true
    readable: false
    payable: false
    payable_by_sc: true
```

One important change:
Instead of writing the ping amount and the pong wait time directly in the scene, we will pull them from environment variables.


## PingAmount and Query

We can now write the final `Scenes` of this tutorial and for this occasion let's introduce a new component: The `ContractQuery` `Step`. This tells MxOps to query the view of a contract and optionally you can save the results for later use and/or print them.

In our situation let's say that we forgot what is the ping amount we need to send to our contract. We could look at the deploy transaction and look at the supplied arguments but that is not very convenient. Instead we will query the ping amount directly from the deployed contract and save this value for when we want to ping.

Such `Step` would look like this:

```yaml
  - type: ContractQuery
    contract: "egld-ping-pong"
    endpoint: getPingAmount
    results_save_key:
      - PingAmount
```

This tells MxOps to save (in the current active `Scenario`) the value from the query result and to attach it to the contract "egld-ping-pong" under the key name "PingAmount".

We can then reuse this value directly during the ping `Step`:

```yaml
  - type: ContractCall
    sender: owner
    contract: "egld-ping-pong"
    endpoint: ping
    gas_limit: 3000000
    value: "%egld-ping-pong.PingAmount"
```

This 'save&reuse' workflow allows you to make very complex and dynamic `Scenes`: it can save you a ton of time in situations like complex and interdependent multi-deployments.

## Transfer Check

MxOps checks by default that a transaction is successful. In our case, we would also like to check that the eGLD transfer was correctly executed during the ping and pong transaction. This can done by specifying a `TransfersCheck` in the `ContractCall` `Step`:

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
          - sender: "owner"
            receiver: "egld-ping-pong"
            token_identifier: EGLD
            amount: "%egld-ping-pong.PingAmount"
```

We take advantages of the variable format of MxOps to specify the value for the transfer. The above check tells MxOps that the transaction should contain only one transfer, and that it should be an eGLD transfer of `PingAmount` token from the user `owner` to the `egld-ping-pong` contract.

```{warning}
By default if checks are not specified by the user, MxOps will run a `SuccessCheck` on each transaction. However if you are using the `checks` keyword, don't forget to add the `SuccessCheck` if you need it!
```

But let's finish our ping `Scene` named `mxops_scenes/02_ping.yaml`:

```yaml
steps:

  - type: ContractQuery
    contract: "egld-ping-pong"
    endpoint: getPingAmount
    results_save_keys:
      - PingAmount

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
          - sender: "%owner.address"
            receiver: "%egld-ping-pong.address"
            token_identifier: EGLD
            amount: "%egld-ping-pong.PingAmount"

```

and our last `Scene` named `mxops_scenes/03_pong.yaml`:

```yaml
steps:

  - type: ContractCall
    sender: owner
    contract: "egld-ping-pong"
    endpoint: pong
    gas_limit: 3000000
    checks:
      - type: Success

      - type: Transfers
        condition: exact
        expected_transfers:
          - sender: "%egld-ping-pong.address"
            receiver: "%owner.address"
            token_identifier: EGLD
            amount: "%egld-ping-pong.PingAmount"

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
│   ├── 01_deploy.yaml
│   ├── 02_ping.yaml
│   ├── 03_pong.yaml
└── wallets
    └── my_devnet_wallet.pem
```

## Execution

To deploy the contract on the devnet, you can enter the following commands:

```bash
export PING_PONG_AMOUNT=1000000000000000000
export PONG_WAIT_TIME=1

mxops execute \
        -n devnet \
        -s mxops_tutorial_enhanced_first_scene \
        mxops_scenes/accounts/devnet.yaml \
        mxops_scenes/01_deploy.yaml
```

In the above command, we have provided the network, the scenario, a first `Scene` where we defined the account related to the devnet and then the `Scene` where the deployment of the contract is defined.

This will give you an output like this:

```bash
MxOps  Copyright (C) 2023  Catenscia
This program comes with ABSOLUTELY NO WARRANTY
[2023-02-24 07:21:10,414 data INFO] Scenario mxops_tutorial_enhanced_first_scene created for network devnet [data:287 in create_scenario]
[2023-02-24 07:21:10,414 scene INFO] Executing scene mxops_scenes/accounts/devnet.yaml [scene:69 in execute_scene]
[2023-02-24 07:21:10,518 scene INFO] Executing scene mxops_scenes/01_deploy.yaml [scene:69 in execute_scene]
[2023-02-24 07:21:10,521 steps INFO] Deploying contract egld-ping-pong [steps:100 in execute]
[2023-02-24 07:21:15,819 steps INFO] Deploy successful on erd1qqqqqqqqqqqqqpgqv2qu073e8vfv82ce2qt4dtcj4dqpga6rplcqvm6swg
tx hash: https://devnet-explorer.multiversx.com/transactions/b0b7c059f44793c03c535f17563dcc349e25972a1ccded6ac812a8c2cd9056c9 [steps:120 in execute]
```

Once your contract is deployed, you can ping it anytime using this command:

```bash
mxops execute \
        -n devnet \
        -s mxops_tutorial_enhanced_first_scene \
        mxops_scenes/accounts/devnet.yaml \
        mxops_scenes/02_ping.yaml
```

```bash
MxOps  Copyright (C) 2023  Catenscia
This program comes with ABSOLUTELY NO WARRANTY
[2023-02-24 07:21:24,667 data INFO] Scenario mxops_tutorial_enhanced_first_scene loaded for network devnet [data:262 in load_scenario]
[2023-02-24 07:21:24,667 scene INFO] Executing scene mxops_scenes/accounts/devnet.yaml [scene:69 in execute_scene]
[2023-02-24 07:21:24,823 scene INFO] Executing scene mxops_scenes/02_ping.yaml [scene:69 in execute_scene]
[2023-02-24 07:21:24,826 steps INFO] Query on getPingAmount for egld-ping-pong [steps:211 in execute]
[2023-02-24 07:21:25,029 steps INFO] Saving Query results as contract data [steps:223 in execute]
[2023-02-24 07:21:25,029 steps INFO] Query successful [steps:231 in execute]
[2023-02-24 07:21:25,030 steps INFO] Calling ping for egld-ping-pong [steps:173 in execute]
[2023-02-24 07:21:35,308 steps INFO] Call successful: https://devnet-explorer.multiversx.com/transactions/bdbc4773fbe05aa8f86f2bbc2d09db26eb50dc1fe4276754acbe17ba106ee65c [steps:188 in execute]
```

And lastly, you can pong the contract:

```bash
mxops execute \
        -n devnet \
        -s mxops_tutorial_enhanced_first_scene \
        mxops_scenes/accounts/devnet.yaml \
        mxops_scenes/03_pong.yaml
```

```bash
MxOps  Copyright (C) 2023  Catenscia
This program comes with ABSOLUTELY NO WARRANTY
[2023-02-24 07:21:24,667 data INFO] Scenario mxops_tutorial_enhanced_first_scene loaded for network devnet [data:262 in load_scenario]
[2023-02-24 07:21:24,667 scene INFO] Executing scene mxops_scenes/accounts/devnet.yaml [scene:69 in execute_scene]
[2023-02-24 07:21:24,823 scene INFO] Executing scene mxops_scenes/03_pong.yaml [scene:69 in execute_scene]
[2023-02-24 07:21:35,308 steps INFO] Calling pong for egld-ping-pong [steps:173 in execute]
[2023-02-24 07:21:40,576 steps INFO] Call successful: https://devnet-explorer.multiversx.com/transactions/95003df0306888d0fb0606f7e6121028b9ac389f9e38b7ee68783fc0e2919e33 [steps:188 in execute]
```

You can notice the extra query `Step` in the logs compared to the first version of this tutorial.

If you wanted to execute all three `Scenes` in a single command call, we would either specify all of them, or just specify the folder of the `Scenes` and MxOps will execute them by alphabetical order.

```bash
mxops execute \
        -n devnet \
        -s mxops_tutorial_enhanced_first_scene \
        mxops_scenes/accounts/devnet.yaml \
        mxops_scenes
```

or

```bash
mxops execute \
        -n devnet \
        -s mxops_tutorial_enhanced_first_scene \
        mxops_scenes/accounts/devnet.yaml \
        mxops_scenes/01_deploy.yaml \
        mxops_scenes/02_ping.yaml \
        mxops_scenes/03_pong.yaml
```

## Data

Let's take a look at the saved data of the current `Scenario`:

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

Ladies and Gentlemen, congratulation for making it until here! It is now time to wrap things up and go towards the 👉 {doc}`conclusion of this tutorial<conclusion>` 🏁
