# Scenario

A `Scenario` is a virtual context that separates contract interactions and in which the results of `step` executions can be stored locally on your computer. This allows to execute identical `Scenes` on different contracts in the **same** network.

## Structure

`Scenario` data is saved locally in the app folder of your computer (the exact path depends on your OS).
This means that wherever you activate MxOps, you will write and read at the same place.

Each `Scenario` has a dedicated file per network. This means that you can run a `Scenario` on the devnet and if you are
satisfied, launch the same `Scenario` on the mainnet without changing any `Scene`.

The files are organized as below:

```bash

<AppFolder>
    |
    mxops
        |
        <Network>
            |
            <my_scenario>.json

```

Where:

- AppFolder is the application folder on your computer (OS dependent, example: share, AppDir ...)
- Network will be the name of chain used (mainnet, devnet, testnet or localnet) for the scenario
- <my_scenario>.json is the file where all the contract data of the executed scenario are stored

```{note}
The files are kept after each executions. This means that you can reuse a `Scenario` and execute new `Scenes` in it. This is very useful for incremental executions (deploy, upgrade...) or recurrent tasks (complex claim/compound cycles for example)
```

```{warning}
This also means that `Scenario` names should be unique per network for all your projects. Otherwise you may encounter data collision.
```

## Commands

`Scenario` can be accessed through the `data` command of MxOps.
Below sections show some command examples. You can always use `mxops data --help` to get more information.

### Existing Scenario

To print out all the existing `Scenario` on a specified network:

```bash
mxops data get -n <network> -l
```

### Scenario Data

To print out all the existing data for a `Scenario` on a specified network:

```bash
mxops data get -n <network> -s <scenario>
```

### Delete Scenario

To delete all the data from a `Scenario`

```bash
mxops data delete -n <network> -s <scenario>
```

### Checkpoints

Sometimes you need to deploy numerous tokens and external contracts to setup your testing
environment. For example when you project relies on xExchange and you want to fully replicate the tokens, pools,
farms and others.
Such setup takes a long time to execute, even when it is automated as most of the transactions have to be made sequentially.

To address this, MxOps has the notion of `Scenario` checkpoints. It allows you to save the data of a scenario in its current state so that you won't need to repeat certain actions.

Here is an example use-case:

1. Execute some `Scenes` that create some tokens
2. Create a checkpoint named `tokens_checkpoint`
3. Execute some `Scenes` that setup some external contracts (ex a wrapper-sc)
4. Create a checkpoint named `external_contracts_checkpoint`
5. Execute the `Scenes` that test your smart-contracts
6. Revert to checkpoint `tokens_checkpoint` or `external_contracts_checkpoint` depending on your needs so that you can use the tokens or the external contracts without creating/deploying them again.

#### Create a Checkpoint

To save the current state of a `Scenario` as a checkpoint.

```bash
mxops data checkpoint -n <network> -s <scenario> -c <checkpoint> -a create
```

#### Load a Checkpoint

Overwrite the current state of a `Scenario` with the data of a checkpoint.

```bash
mxops data checkpoint -n <network> -s <scenario> -c <checkpoint> -a load
```

```{warning}
Checkpoint only save the local data of a `Scenario`, it does not perform any blockchain
operation: It can not revert a smart-contract in a certain state. If your scenario needs
every contracts to be as new, you will need to redeploy them each time.
```
