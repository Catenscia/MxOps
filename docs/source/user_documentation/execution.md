# Execution

Once you have written your scenes, the only thing left for you is to pass them to MxOps for execution.

When executing scenes, you will need to supply a network, a scenario and any number of scenes or folders of scenes.

```bash
mxops execute [-h] -s SCENARIO -n NETWORK [-c] [-d] elements [elements ...]
```



| Argument     | Short Handle | Description                                                                | Allowed values                                       |
|--------------|--------------|----------------------------------------------------------------------------|------------------------------------------------------|
| `--scenario` | `-s`         | Mandatory, the name of the scenario in which the execution will take place | Any alpha-numerical string                           |
| `--network`  | `-n`         | Mandatory, the MultiversX network onto which the execution will take place | mainnet, devnet, testnet, localnet, chain-simulator  |
| `--clean`    | `-c`         | Optional, clean (delete) the data of the scenario before the execution     | NA                                                   |
| `--delete`   | `-d`         | Optional, delete the data of the scenario after the execution              | NA                                                   |

You can supply as many elements as you want for the execution. An element can be a scene (yaml file)
or a folder of scenes. In case you are providing a folder of scenes, the scenes will be executed in the alpha-numeric order of the files names. 

## Examples

### Single Scene

```bash
mxops \
    execute \
    -n mainnet \
    -s my_scenario \
    path/to/my_scene.yaml
```

### Multiple Scenes

```bash
mxops \
    execute \
    -n mainnet \
    -s my_scenario \
    path/to/my_scene_1.yaml \
    path/to/my_scene_2.yaml
```

### Folder of Scenes

```bash
mxops \
    execute \
    -n testnet \
    -s my_scenario \
    path/to/my_folder_of_scenes
```

### Folders of Scenes and Scenes

```bash
mxops \
    execute \
    -n devnet \
    -s integration_tests \
    integration_tests/scenes/accounts/devnet_accounts.yaml \
    integration_tests/test_1_scenes \
    integration_tests/reset_contract_scene.yaml \
    integration_tests/test_2_scenes \
```

### Clean Scenario

```bash
mxops \
    execute \
    -n devnet \
    -s integration_tests \
    -c \
    path/to/my_scene.yaml
```

### Delete Scenario


```bash
mxops \
    execute \
    -n devnet \
    -s integration_tests \
    -d \
    path/to/my_scene.yaml
```
