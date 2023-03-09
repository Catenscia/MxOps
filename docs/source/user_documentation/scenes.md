# Scenes

A `Scene` is a collection of sequential `Steps` to be executed by MxOps.
At execution time, the user will designate the `Scenario` in which the actions will be performed and the data recorded.

## Scene Format

`Scenes` are written in yaml format. Each file will contain the following elements:

- `allowed_network*`: a list of the network onto which the `Scene` is allowed to be run. Allowed values are: [`LOCAL`, `TEST`, `DEV`, `MAIN`].
- `allowed_scenario*`: a list of the scenario into which the `Scene` is allowed to be run. Regex can be used here.
- `accounts`: a list of the accounts details. This can be defined only once per execution (so in only one file in the case where several files were submitted). Each account will be designated by its `account_name` in the `Steps`.
- `external_contracts`: a dictionary of external contract addresses. The keys will be used as contract ids by MxOps. This can be defined only once per scenario.
- `steps`: a list the `Steps` to execute sequentially.

 \* *mandatory values*

## Scene Example

```yaml

# list of network onto which this scene can be run
allowed_networks:
  - MAIN
  - DEV

# list of scenario into which this scene can be run
allowed_scenario:
  - ".*"  # regex allowed here (in this case ".*" allows everything)

# list of accounts details. To be defined only once per execution
# In case of the execution of several scenes. This can be defined in a single file.
# names have to be unique or they will override each other
accounts:
  - account_name: bob
    pem_path: path/to/bom_pem
  - account_name: alice
    ledger_account_index: 12
    ledger_address_index: 2

# external contracts that will be called for transactions or queries in future steps
external_contracts:
  egld_wrapper: erd1qqqqqqqqqqqqqpgqhe8t5jewej70zupmh44jurgn29psua5l2jps3ntjj3 
  xexchange_router: erd1qqqqqqqqqqqqqpgqq66xk9gfr4esuhem3jru86wg5hvp33a62jps2fy57p

# list of the steps to execute
steps:
  - type: ContractDeploy
    sender: bob
    wasm_path: path/to/wasm
    contract_id: my_first_sc
    gas_limit: 1584000
    arguments:
      - arg1
      - arg2
    upgradeable: True
    readable: False
    payable: False
    payable_by_sc: False

  - type: ContractCall
    sender: alice
    contract: my_first_sc
    endpoint: myEndpoint
    gas_limit: 60000000
    arguments:
      - arg1
      - arg2
```
