# About Scenario

When you executed you first `Scene`, you may have asked yourself some questions along these lines:

- What happen if I enter a second time the command to execute the `Scene`?
- Let's say I want to ping or pong my contract again, how do I do that without deploying a new contract ?

`Scenarios` are here to answer these needs and many more 😁

This section will give you a basic understanding of `Scenarios`, you can always read later on the complete section on `Scenarios` in the user documentation chapter.

## Definition

`Scenarios` are virtual context in which data can be saved and reused. The first use case is during deployment: Once a contract is deployed, one needs to save the address that has been assigned to the contract for later interactions.

`Scenarios` save contract data by `contract_id`. This means that the same `contract_id` can be use in different `Scenarios` but also in different networks (main, dev...). However, if you try to assign twice the same `contract-id` within the same `Scenario`, MxOps will throw an error.
This allows maximum reusability for the `Scenes` as you don't have to monitor which ids has already been taken in your others `Scenarios`.

## Persistence

Unless you specifically decide to delete it, the data stored in a `Scenario` is persistent on your local computer. You can access from it everywhere on your computer 💻.

For example, we can see what data has been saved when we executed our first `Scene`. Try this command:

```bash
mxops data get -n devnet -s mxops_tutorial_first_scene
```

This will give you the following output (you may have more or less data depending of your version of MxOps):

```bash
MxOps  Copyright (C) 2023  Catenscia
This program comes with ABSOLUTELY NO WARRANTY
[2023-02-24 18:07:55,003 data INFO] Scenario mxops_tutorial_first_scene loaded for network devnet [data:262 in load_scenario]
{
    "name": "mxops_tutorial_first_scene",
    "network": "devnet",
    "creation_time": 1677134890,
    "last_update_time": 1677134896,
    "contracts_data": {
        "egld-ping-pong": {
            "contract_id": "egld-ping-pong",
            "address": "erd1qqqqqqqqqqqqqpgq0048vv3uk6l6cdreezpallvduy4qnfv2plcq74464k",
            "saved_values": {},
            "wasm_hash": "5ce403a4f73701481cc15b2378cdc5bce3e35fa215815aa5eb9104d9f7ab2451",
            "deploy_time": 1677134892,
            "last_upgrade_time": 1677134892,
            "is_external": false
        }
    },
    "tokens_data": {}
}
```

You can see that our `Scenario` has only one contract at the moment: it is the ping-pong contract we deployed earlier.

If you were to execute other `Scenes` in the scenario `mxops_tutorial_first_scene` you will be able to reference to the deployed contract by simply using its `contract_id`. In fact that is already what you have been doing when using `ContractCalls`:

```yaml
  - type: ContractCall
    sender: owner
    contract: "egld-ping-pong"  # the contract_id is used instead of the bech32 address
    endpoint: pong
    gas_limit: 3000000
```

And the better part is that you can also save query results in a `Scenario` and use these results in later interactions.

 So now that `Scenarios` have been introduced to you, we are going to take a look again at our first `Scene` and improve it to make it much more practical: let's head to the 👉 {doc}`next section!<enhanced_first_scene>` 👈
