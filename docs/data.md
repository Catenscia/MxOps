# Data

One of the benefits of using MvxOps is to manage several scenarios without data collision.
This means that you can deploy a contract on the mainnet, run a gas test scenario on a local testnet, run operational tests on the devnet (or the local testnet again) and keep track of all the important data generated within these scenario such as contract address, tickers of created tokens, queries results and so on...

## Structure

The contract data is saved locally in the app folder of your computer (the exact path depends on your OS).
This means that wherever you activate MvxOps, you will write and read at the same place.

The contract data is saved in regards to the scenario in which it was generated.

Each scenario has a dedicated file per network. This means that you can run a scenario on the devnet and if you are
satisfied, launch the same scenario on the mainnet without changing any file.

The files organised as below:

```bash

<AppFolder>
    |
    mvxops
        |
        <Network>
            |
            <my_scenario>.json
        
```

Where:

- AppFolder is the application folder on your computer (OS dependent, example: share, AppDir ...)
- Network will be the name of chain used (MAIN, DEV, TEST or LOCAL) for the scenario
- <my_scenario>.json is the file where all the contract data of the executed scenario are stored

One important note: the files are kept after each executions. This means that you can reuse a scenario and execute new scenes
in it. This is very usefull for incremental executions (deploy, upgrade...) or reccurent tasks (complexe claim/compound cycles for example)

## Scenario File Structure

The file of a scenario is organised as below

```json
{
    "name": "<name_of_the_scenario>",
    "network": "<name_of_the_network>",
    "creation_time": "<timestamp>",
    "last_update_time": "<timestamp>",
    "contracts": {
        "contract_id_1": {
            "id": "contract_id_1",
            "address": "<bech32_contract_address>",
            "wasm_hash": "<last_uploaded_contract_hash>",
            "deploy_time": "<timestamp>",
            "last_upgrade_time_": "<timestamp>",
            "saved_values": {
                "key_1": "value_1",
                "key_2": "value_2"
            }
        }
    }
}
```
