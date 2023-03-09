# Execution

Once you have written your `Scenes`, the only thing left for you is to pass them to MxOps for execution.

When executing `Scenes`, you will need to supply a network, a scenario and any number of `Scenes` or folders of `Scenes`.

```bash
mxops execute [-h] -s SCENARIO -n NETWORK elements [elements ...]
```

Below are some examples.

## Single Scene

```bash
mxops \
    execute \
    -n MAIN \
    -s compound_scenario \
    counpound_scene.yaml
```

## Accounts Scene and Folder

```bash
mxops \
    execute \
    -n TEST \
    -s integration_tests \
    integration_tests/scenes/accounts/testnet_accounts.yaml \
    integration_tests/scenes
```

## Accounts Scene, Folders and Files

```bash
mxops \
    execute \
    -n DEV \
    -s integration_tests \
    integration_tests/scenes/accounts/devnet_accounts.yaml \
    integration_tests/test_1_scenes \
    integration_tests/reset_contract_scene.yaml \
    integration_tests/test_2_scenes \
```
