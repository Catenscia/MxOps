# First Scenes

Finally, let's get into it! In this chapter, you will learn how to write your first very simple scenes. Our goal is to achieve the following with MxOps:

- create a new wallet on shard 1
- claim some devnet EGLD for our new wallet
- wrap some EGLD to obtain WEGLD
- unwrap the obtained WEGLD

These are very simple actions, but as they a very often needed, they are perfect for our first MxOps scenes 😁

## Setup

Create a new directory

```bash
mkdir mxops_first_scene
cd mxops_first_scene
```

Create a new directory for our scenes, and create the first yaml file, which will be our first scene:

```bash
mkdir scenes
touch scenes/01_setup.yaml
```

### Account designation

This first element to write in our setup scene will be to declare the wrapper contract that we are going to use. We will choose the [wrapper contract on the shard 1 of devnet](https://devnet-explorer.multiversx.com/accounts/erd1qqqqqqqqqqqqqpgqpv09kfzry5y4sj05udcngesat07umyj70n4sa2c0rp), and we will give it an easier designation than its address: let's name it egld_wrapper.

For MxOps, egld_wrapper will become the account id of the wrapper contract `erd1qq...0rp` and we can use the address or the account id interchangeably.

```yaml
accounts:
  - account_id: egld_wrapper
    address: erd1qqqqqqqqqqqqqpgqpv09kfzry5y4sj05udcngesat07umyj70n4sa2c0rp
```

### Steps

After this, we will declare in our scene the different steps (aka actions) that we want MxOps to execute. For the setup, we will have two steps:

- create a wallet on shard 1
- claim some devnet EGLD from a faucet

```yaml
steps:
  - <step1>
    ...

  - <step_2>
    ...

```

The two next sections will define these steps.

#### Wallet Generation

To create a new wallet, we will use the [GenerateWallets step](generate_wallets_target):

```yaml
  - type: GenerateWallets
    save_folder: ./wallets
    wallets:
        - user
    shard: 1
```

This will create a new wallet at `./wallets/user.pem`. As specified, this wallet will be on shard 1, which will make transactions with the wrapper faster as the wrapper is also on shard 1.
This new wallet will automatically be assigned the account id `user`, so we can simply reference this wallet by this account id later on.

#### Faucet

To get funds for our new wallet, we will use the [R3d4 faucet step](r3d4_faucet_target), which is a community faucet on devnet and on testnet.

```yaml
  - type: R3D4Faucet
    targets:
      - user
```

```{note}
Please do not abuse this faucet, as it is really useful for the community. If you have left-over funds, don't hesitate to send them back to the address that initially gave them to you.
```

### Full scene

To sum up, this is what our setup scene look like:

`scenes/01_setup.yaml`
```yaml
accounts:
  - account_id: egld_wrapper
    address: erd1qqqqqqqqqqqqqpgqpv09kfzry5y4sj05udcngesat07umyj70n4sa2c0rp

steps:

  - type: GenerateWallets
    save_folder: ./wallets
    wallets:
        - user
    shard: 1
  
  - type: R3D4Faucet
    targets:
      - user
```

### Execution

To execute this scene, use the command below

```bash
mxops execute -n devnet -s first_scenario scenes/01_setup.yaml
```

```{dropdown} Command results
:class-title: normal-title
:color: light

```bash
[2025-03-26 16:37:42,899 INFO] MxOps  Copyright (C) 2025  Catenscia
This program comes with ABSOLUTELY NO WARRANTY [general in main_cli.py:65]
[2025-03-26 16:37:42,899 INFO] Deletion of the scenario first_scenario on devnet [data in execution_data.py:898]
[2025-03-26 16:37:42,899 INFO] Scenario deleted [data in execution_data.py:910]
[2025-03-26 16:37:42,899 INFO] Scenario first_scenario created for network devnet [data in execution_data.py:861]
[2025-03-26 16:37:42,899 INFO] Executing scene scenes/01_setup.yaml [execution in scene.py:148]
[2025-03-26 16:37:42,977 INFO] Wallet n°1/1 generated with address erd17jzayrcrduwmekfldncqvqd5g2kjw24ujuw9nz93df6c3vv3xkzsshcp7d at wallets/user.pem [execution in setup.py:84]
[2025-03-26 16:37:43,064 INFO] Requesting 1.0 dEGLD from r3d4 faucet for erd17jzayrcrduwmekfldncqvqd5g2kjw24ujuw9nz93df6c3vv3xkzsshcp7d [execution in setup.py:133]
[2025-03-26 16:37:43,133 INFO] Response from faucet: Added to list [execution in setup.py:174]
[2025-03-26 16:37:43,133 INFO] Check the account for funds arrival: https://devnet-explorer.multiversx.com/accounts/erd17jzayrcrduwmekfldncqvqd5g2kjw24ujuw9nz93df6c3vv3xkzsshcp7d [execution in setup.py:140]
```

On the last line logged by MxOps, you can see an explorer link to the account that you created. Click on it and you should see some devnet EGLD arriving on your account within 10-20s.

```{note}
If the faucet is empty, you can still manually claim funds on the [official devnet wallet](https://devnet-wallet.multiversx.com/faucet)
```

## Wrap & Unwrap

Now that we have setup our account, we can interact with the wrapper contract.
Let's create a second scene:

```bash
touch scenes/02_wrap_unwrap.yaml
```

### Wrapping

To wrap EGLD, we will use a [ContractCall step](contract_call_target)


```yaml
steps:
  
  - type: ContractCall
    sender: user
    contract: egld_wrapper
    endpoint: wrapEgld
    gas_limit: 6000000
    value: 100000000000000000  # 0.1 EGLD
```

With this step, we are saying to MxOps to make a transaction from our user account, to the egld_wrapper contract. It will call the endpoint wrapEgld, while sending 0.1 EGLD. The EGLD amount has to be provided in the full integer form: as EGLD has 18 decimals, this gives 100000000000000000.

### Unwrapping

The same [ContractCall step](contract_call_target) will be used to unwrap the tokens, except that this time we are not going to send EGLD but WEGLD. This changes things a little because WEGLD is an ESDT (eStandard Digital Token) while EGLD is the native token of MultiversX. To send WEGLD, we will provide its devnet identifier (WEGLD-a28c59) and the amount we want to send (0.1 WEGLD so 100000000000000000 in full integer form).

```yaml
  - type: ContractCall
    sender: user
    contract: egld_wrapper
    endpoint: unwrapEgld
    gas_limit: 6000000
    esdt_transfers: 
      - identifier: WEGLD-a28c59
        amount: 100000000000000000  # 0.1 WEGLD
```

### Full Scene

To sum up, this is what our wrapping/unwrapping scene look like:

`scenes/02_wrap_unwrap.yaml`
```yaml
steps:
  
  - type: ContractCall
    sender: user
    contract: egld_wrapper
    endpoint: wrapEgld
    gas_limit: 6000000
    value: 100000000000000000  # 0.1 EGLD
  
  - type: ContractCall
    sender: user
    contract: egld_wrapper
    endpoint: unwrapEgld
    gas_limit: 6000000
    esdt_transfers: 
      - identifier: WEGLD-a28c59
        amount: 100000000000000000  # 0.1 WEGLD
```

### Execution

To execute this scene, use the command below

```bash
mxops execute -n devnet -s first_scenario scenes/02_wrap_unwrap.yaml
```

```{dropdown} Command results
:class-title: normal-title
:color: light

```bash
[2025-03-26 16:38:30,596 INFO] MxOps  Copyright (C) 2025  Catenscia
This program comes with ABSOLUTELY NO WARRANTY [general in main_cli.py:65]
[2025-03-26 16:38:30,596 INFO] scenario first_scenario loaded for network devnet [data in execution_data.py:833]
[2025-03-26 16:38:30,596 INFO] Executing scene scenes/02_wrap_unwrap.yaml [execution in scene.py:148]
[2025-03-26 16:38:30,598 INFO] Calling wrapEgld on erd1qqqqqqqqqqqqqpgqpv09kfzry5y4sj05udcngesat07umyj70n4sa2c0rp (egld_wrapper)  [execution in smart_contract.py:243]
[2025-03-26 16:38:30,598 INFO] account erd17jzayrcrduwmekfldncqvqd5g2kjw24ujuw9nz93df6c3vv3xkzsshcp7d is missing, reloading from scenario data [execution in account.py:138]
[2025-03-26 16:38:33,838 INFO] Transaction successful: https://devnet-explorer.multiversx.com/transaction/fbc79b1951e154681c18f73f9734ab9b5b591d2e9a71d531b63f97649d3fdaa1 [execution in base.py:163]
[2025-03-26 16:38:33,841 INFO] Calling unwrapEgld on erd1qqqqqqqqqqqqqpgqpv09kfzry5y4sj05udcngesat07umyj70n4sa2c0rp (egld_wrapper)  [execution in smart_contract.py:243]
[2025-03-26 16:38:40,051 INFO] Transaction successful: https://devnet-explorer.multiversx.com/transaction/b481527427c8ca40bce0159e70839ae0c74feb9a3f801420e1896adbd2c80e10 [execution in base.py:163]
```

By default, MxOps will wait for confirmation after each transaction is sent. If the transaction fails, MxOps will stop the execution and display the faulty transaction. 

Click on the transactions links in the logs to observe what happened on devnet when you executed the scene!

## About Scenario

You may have asked yourself some questions when executing the MxOps commands or when looking at the logs:


>Why didn't we specify the user or the contract id again in the second scene?

>MxOps logged this line, what does it means ? 
>`account erd17...p7d is missing, reloading from scenario data`

>What is this `-s first_scenario` parameter?

The answer to all of these questions lies in the scenario concept of MxOps: A scenario is a virtual data context, saved locally on your computer, in which MxOps will save values. For example, MxOps will save within a scenario the account ids, the account access (ex pem or ledger), the address of newly deployed contracts and much more!

When executing the first scene, you told MxOps to save the account ids (user and egld_wrapper) and the account access (./wallets/user.pem) to the scenario named first_scenario.

So when you executed the second scene in the same scenario, MxOps already had all the information he needed to get access to the wallet and to know who where behind the ids egld_wrapper and user.

Scenario are a vast topic and one of the key strength of MxOps. Don't hesitate to look at the [chapter dedicated to scenario](../user_documentation/scenario) later on.

But for, now, let's head to the 👉 [conclusion of this introduction to MxOps](conclusion) 🏁



