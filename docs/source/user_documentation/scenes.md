# Scenes

A scene is mostly a collection of sequential steps to be executed by MxOps.
At execution time, the user will designate the scenario and the network in which the actions will be performed and the data recorded.

## Scene Format

scenes are written in yaml format. Each file can contain the following elements:

- `allowed_network`: a list of the networks onto which the scene is allowed to be run. Allowed values are: `mainnet`, `devnet`, `testnet`, `localnet` and `chain-simulator`. By default all networks except mainnet are allowed.
- `allowed_scenario`: a list of the scenarios into which the scene is allowed to be run. Regex can be used here. By default all scenarios are allowed.
- `accounts`: a list to define either signer accounts (pem wallet, ledger wallet, ...) or just ids for easier interaction (account id and ABIs for third party contracts, ...).
- `steps`: a list of the the steps to execute sequentially.

All of the above elements are optional, you can use only the one you need and omit the rest.

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

# List of the accounts that will be used in this scene or in other scenes later on. This means that
# if you execute a folder of scenes for example, you only need to define the accounts
# in the first executed scene.
# Ids have to be unique per scenario
accounts:

  # a pem wallet
  - account_id: bob
    pem_path: path/to/bom_pem

  # a keystore wallet (password from environment variable for security)
  - account_id: carol
    keystore_path: path/to/carol_keystore.json
    password_env_var: CAROL_KEYSTORE_PASSWORD  # name of the env var containing the password
    address_index: 0  # optional, for mnemonic-based keystores

  # a ledger wallet
  - account_id: alice
    ledger_address_index: 2

  # a folder of pem wallets
  - name: user_wallets  # the list of the loaded wallets names will be saved under this name
    folder_path: ./path/to/all/users_wallets

  # a third party account
  - account_id: beni
    address: erd159u4p8d6agj2jekf5fmgpscpgeq7ytnv65yy8ajme2x8r7qwqensulfejs

  # a third party contract abi
  - account_id: egld_wrapper
    address: erd1qqqqqqqqqqqqqpgqhe8t5jewej70zupmh44jurgn29psua5l2jps3ntjj3 
    abi_path: abis/egld_wrapper.abi.json

  # a third party contract without abi
  - account_id: xexchange_router
    address: erd1qqqqqqqqqqqqqpgqq66xk9gfr4esuhem3jru86wg5hvp33a62jps2fy57p

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
