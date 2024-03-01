# First Scene

In this section, we will write a simple `Scene` to deploy and interact with the ping-pong contract from the [MultiversX tutorial](https://docs.multiversx.com/developers/tutorials/your-first-dapp).

Here is the plan:

- Deploy the ping-pong contract
- Ping some eGLD to the contract
- Pong the eGLD back

Nothing fancy there, but this will teach you the strings of MxOps and you will get familiar with this tool 😄

## Folder

In this tutorial, we will create some files and clone a git repository. To keep things nice and tidy, we'll create a new folder. Let's say `mxops_tutorial` for example.

## Owner Wallet

We will need a wallet to make our tests. The easiest is to use a pem wallet, as it doesn't require a confirmation when signing transactions:

```bash
mkdir wallets
mxpy wallet derive wallets/my_devnet_wallet.pem
```

```{warning}
The secret key is written in clear in a pem file! It is very useful for tests but unless you know what you are doing, don't use pem files for the mainnet.
```

We will execute this tutorial on the devnet, so the account you just created will need some devnet eGLD. You an use the faucet on the [devnet wallet](https://devnet-wallet.multiversx.com) to get some.

```{thumbnail} ../images/devnet_faucet.png
```

## Smart Contract Build

To deploy a smart-contract, we need it in wasm format.
Let's retrieve from Github the source code of the ping-pong contract and compile it:

```bash
git clone https://github.com/multiversx/mx-ping-pong-sc contract
cd contract/ping-pong
sc-meta all build
cd ../../
```

Make sure that the last lines of the output are like this:

```bash
Packing ../output/ping-pong.mxsc.json ...
Contract size: 3799 bytes.  # size maybe a bit different depending on the version
```

The contract is now compiled and ready to be deployed! 📡

## Scene

Everything is in place for us to create our first `Scene` so let's get to work ⚒️👷‍♂️

For this, create a file named `first_scene.yaml`. This file will contain you first `Scene` and your folder should now look like this:

```text
mxops_tutorial
├── contract
│   ├── ping-pong
│   │   ├── output
│   │   │   ├── ping-pong.abi.json
│   │   │   └── ping-pong.wasm
│   │   ...
│   ...
├── wallets
│   └── my_devnet_wallet.pem
└── first_scene.yaml
```

### Blockchain Network

The first element we specify in a `Scene` is the network(s) onto which it is allowed to run.
As said above, we will work on the devnet so write these lines at the top of the `Scene`:

```yaml
allowed_networks:
    - devnet
```

We will also add the following lines, but you don't have to bother with what they do at the moment.

```yaml
allowed_scenario:
    - mxops_tutorial_first_scene
```

### Wallet

The next thing we can specify in a `Scene` is a list of wallets we will use later on. Here we have only one wallet and we will use it to deploy the ping-pong contract so we will name it `owner`.

```yaml
accounts:
  - account_name: owner
    pem_path: ./wallets/my_devnet_wallet.pem
```

### Steps

We want to perform three actions: one deployment and two contract calls. In MxOps, any action is called a `Step`.
In other words, a `Scene` contains a series of `Steps` that tells what MxOps should do.

#### Step 1: Deployment

To deploy our contract, we will use a `ContractDeploy` `Step` while specifying several elements: the path of the wasm file, the wallet that will deploy the contract, the code metadata and lastly the arguments for the initialization of our contract.

The `init` function of the `ping-pong`contract take three arguments:

```rust
#[init]
fn init(
    &self,
    ping_amount: BigUint,
    duration_in_seconds: u64,
    opt_token_id: OptionalValue<EgldOrEsdtTokenIdentifier>,
)
```

We will specify 0.5 eGLD for the ping amount and 1 seconds for the duration to enable us to pong right after the ping.
To be able to interact with the deployed contract later on in the scene, we need give the newly deployed contract an id.  We will choose "egld-ping-pong" for our case.

The `ContractStep` will look like this:

```yaml
  - type: ContractDeploy
    sender: owner
    wasm_path: "./contract/ping-pong/output/ping-pong.wasm"
    contract_id: "egld-ping-pong"
    gas_limit: 50000000
    arguments:
      - 500000000000000000 # 0.5eGLD
      - 1 # 1 sec
    upgradeable: true
    readable: false
    payable: false
    payable_by_sc: true
```

#### Step 2: Ping

Once our contract is deployed, we can ping it. This will be done with a `ContractCall` `Step` where we specify the contract we want to call, the endpoint and the potential arguments and transfers. Here, we will call the endpoint `ping` while sending 0.5eGLD.

```yaml
  - type: ContractCall
    sender: owner
    contract: "egld-ping-pong"
    endpoint: ping
    gas_limit: 100000000
    value: 500000000000000000 # 0.5eGLD
```

#### Step 3: Pong

As we set a wait time of 1 second and a block confirmation time is more than that, we can call the "pong" endpoint immediately after the ping confirmation.

We will use again a `ContractCall` `Step` but this time for the `pong` endpoint which doesn't needs any arguments nor transfers.

```yaml
  - type: ContractCall
    sender: owner
    contract: "egld-ping-pong"
    endpoint: pong
    gas_limit: 100000000
```

With this, we finished our first scene and your file `first_scene.yaml` should now look like this:

```yaml
allowed_networks:
    - devnet

allowed_scenario:
    - mxops_tutorial_first_scene

accounts:
  - account_name: owner
    pem_path: ./wallets/my_devnet_wallet.pem

steps:

  - type: ContractDeploy
    sender: owner
    wasm_path: "./contract/ping-pong/output/ping-pong.wasm"
    contract_id: "egld-ping-pong"
    gas_limit: 3000000
    arguments:
      - 500000000000000000
      - 1
    upgradeable: true
    readable: false
    payable: false
    payable_by_sc: true

  - type: ContractCall
    sender: owner
    contract: "egld-ping-pong"
    endpoint: ping
    gas_limit: 3000000
    value: 500000000000000000

  - type: ContractCall
    sender: owner
    contract: "egld-ping-pong"
    endpoint: pong
    gas_limit: 3000000

```

### Execution

The only thing left to do for us is now to tell MxOps to execute our scene. We will give it the network, a name for a `Scenario` and the path to our `Scene` file.

```{note}
🙋 "Wait wait, You still did not explain what is a `Scenario`?!?" 

Yes this is true, but it will come it due time, don't worry 🫡
```

This is the command to execute your scene:

```bash
mxops execute \
        -n devnet \
        -s mxops_tutorial_first_scene \
        first_scene.yaml
```

You should now see MxOps slowly executing the steps, one after the other. It will also give you the explorer links of the transactions so you can inspect the results in more details if you want to.

Once finished, the output of your console should look like this:

```bash
MxOps  Copyright (C) 2023  Catenscia
This program comes with ABSOLUTELY NO WARRANTY
[2023-02-23 07:48:10,748 data INFO] Scenario mxops_tutorial_first_scene created for network devnet [data:287 in create_scenario]
[2023-02-23 07:48:10,749 scene INFO] Executing scene first_scene.yaml [scene:69 in execute_scene]
[2023-02-23 07:48:10,849 steps INFO] Deploying contract egld-ping-pong [steps:100 in execute]
[2023-02-23 07:48:16,198 steps INFO] Deploy successful on erd1qqqqqqqqqqqqqpgq0048vv3uk6l6cdreezpallvduy4qnfv2plcq74464k
tx hash: https://devnet-explorer.multiversx.com/transactions/c0b3a84c2a2b0c38d4464ce1de8e715cbab0491ad47725f75dddbde7f2a7304c [steps:120 in execute]
[2023-02-23 07:48:16,200 steps INFO] Calling ping for egld-ping-pong [steps:173 in execute]
[2023-02-23 07:48:21,395 steps INFO] Call successful: https://devnet-explorer.multiversx.com/transactions/03e71b6fc2250303e6aee0e256c6391074c9cef7037e6622341b0700c202da4d [steps:188 in execute]
[2023-02-23 07:48:21,396 steps INFO] Calling pong for egld-ping-pong [steps:173 in execute]
[2023-02-23 07:48:26,663 steps INFO] Call successful: https://devnet-explorer.multiversx.com/transactions/63704f9276dc268ed9a133c476e2956fdffc489051684022aff5793ec49544ef [steps:188 in execute]
```

```{note}
By default, MxOps checks that each transaction is successful. In case an unexpected error is encountered, the execution will be stopped.
```

Congratulation you wrote and executed your first `Scene` with MxOps 🎉🎉🎉

Next, we will **finally** explain the mystery behind `Scenarios`! See you {doc}`there<about_scenarios>` 😀
