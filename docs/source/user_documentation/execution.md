# Execution

Once you have written your `Scenes`, the only thing left for you is to pass them to MxOps for execution.

When executing `Scenes`, you will need to supply a network, a scenario and any number of `Scenes` or folders of `Scenes`.

```bash
mxops execute [-h] -s SCENARIO -n NETWORK [-c] [-d] elements [elements ...]
```

| Argument     | Short Handle   | Description                                                     |
|--------------|----------------|-----------------------------------------------------------------|
| `--scenario` | `-s`           | Mandatory, the name of the `Scenario` in which the execution<br>will take place |
| `--network`  | `-n`           | Mandatory, the MultiversX network onto which the execution<br>will take place   |
| `--clean`    | `-c`           | Optional, clean (delete) the data of the `Scenario` before<br>the execution     |
| `--delete`   | `-d`           | Optional, delete the data of the `Scenario` after the execution |

You supply as many elements as you want for the execution. An element can be a `Scene` (yaml file)
or a folder of `Scenes`. You will find below some examples.

## Single Scene

```bash
mxops \
    execute \
    -n mainnet \
    -s compound_scenario \
    counpound_scene.yaml
```

## Accounts Scene and Folder

```bash
mxops \
    execute \
    -n testnet \
    -s integration_tests \
    -c \
    integration_tests/scenes/accounts/testnet_accounts.yaml \
    integration_tests/scenes
```

## Accounts Scene, Folders and Files

```bash
mxops \
    execute \
    -n devnet \
    -s integration_tests \
    -c \
    -d \
    integration_tests/scenes/accounts/devnet_accounts.yaml \
    integration_tests/test_1_scenes \
    integration_tests/reset_contract_scene.yaml \
    integration_tests/test_2_scenes \
```
