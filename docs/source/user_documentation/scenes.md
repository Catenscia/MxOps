# Scenes

A `Scene` is a collection of sequential `Steps` to be executed by MxOps.
At execution time, the user will designate the `Scenario` in which the actions will be performed and the data recorded.

## Scene Format

`Scenes` are written in yaml format. Each file can contain the following elements:

- `allowed_network`: a list of the networks onto which the `Scene` is allowed to be run. Allowed values are: [`mainnet`, `devnet`, `testnet`, `localnet`, `chain-simulator`]. By default all networks except the mainnet are allowed.
- `allowed_scenario`: a list of the scenario into which the `Scene` is allowed to be run. Regex can be used here. By default all scenario are allowed.
- `accounts`: a list of the accounts details. This can be defined only once per execution (so in only one file in the case where several files were submitted). Each account will be designated by its `account_id` in the `Steps`.
- `external_contracts`: a dictionary of external contract addresses. The keys will be used as contract ids by MxOps. This can be defined only once per scenario.
- `steps`: a list the `Steps` to execute sequentially.

All of the above elements are optional, you can use only the one you need.

## Scene Example

```yaml

# List of network onto which this scene can be run
allowed_networks:
  - mainnet
  - devnet

# List of scenario into which this scene can be run
# Regex can be used. For example ".*" allows all scenario.
allowed_scenario:
    - "<scenario_name_or_regex>"
    - "<scenario_name_or_regex>"

# List of the accounts that will be used in this scene or in other scenes later scenes. This means that
# if you execute a folder of scenes for example, you only need to define the accounts in the first executed scene.
# Names have to be unique or they will override each other
accounts:
  - account_id: bob
    pem_path: path/to/bom_pem

  - account_id: alice
    ledger_address_index: 2

  - name: user_wallets
    folder_path: ./path/to/all/users_wallets  # all the pem wallet of the folder will be loaded using the file names as account names

# External contracts that will be called for transactions or queries in future steps
external_contracts:
  egld_wrapper: erd1qqqqqqqqqqqqqpgqhe8t5jewej70zupmh44jurgn29psua5l2jps3ntjj3 
  xexchange_router: erd1qqqqqqqqqqqqqpgqq66xk9gfr4esuhem3jru86wg5hvp33a62jps2fy57p

# List of the steps to execute in this scene
steps:
  - type: ContractDeploy
    sender: bob
    wasm_path: path/to/wasm
    contract_id: my_first_sc
    gas_limit: 1584000
    arguments:
      - arg1
      - arg2
    upgradeable: true
    readable: false
    payable: false
    payable_by_sc: false

  - type: ContractCall
    sender: alice
    contract: my_first_sc
    endpoint: myEndpoint
    gas_limit: 60000000
    arguments:
      - arg1
      - arg2
```
