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
mxops data get -n <NETWORK> -l
```

### Scenario Data

To print out all the existing data for a `Scenario` on a specified network:

```bash
mxops data get -n <NETWORK> -s <scenario>
```

### Delete Scenario

To delete all the data from a `Scenario`

```bash
mxops data delete -n <NETWORK> -s <scenario>
```
