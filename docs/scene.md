# Scene

A scene is a collection of sequential steps to be executed by MvxOps.
When executing a scene, the user will designate the scenario in which the actions and the data will be recorded.

## Scene Format

Scene are written in yaml format. The file will contain generic information about the scene and the list of steps to execute during the scene.

```yaml

# list of network onto which this scene can be run
allowed_networks:
  - MAIN
  - DEV

# list of scenario into which this scene can be run
allowed_scenario:
  - "*"  # regex allowed here

# list of accounts details. To be defined only once per execution
# In case of the execution of several scenes. This can be defined in a single file.
# names have to be unique or they will override each other
accounts:
  - account_name: bob
    pem_path: path/to/bom_pem
  - account_name: alice
    ledger_account_index: 12
    ledger_address_index: 2

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
    sender:
      pem_path: path/to/pem
    contract_id: my_first_sc
    endpoint: myEndpoint
    gas_limit: 60000000
    arguments:
      - arg1
      - arg2
```

## Steps

Several type of steps exists, to allow users to easily construct complexe scenes.
If you feel something is missing, please make a suggestion in the github!

### Contract Deploy Step

The steps tells MvxOps to deploy a contract. The address of the new contract will be
saved under the provided id to allow futur interaction.

```yaml
type: ContractDeploy
sender: bob
content:
wasm_file: path/to/wasm
contract_id: my_first_sc
gas_limit: 1584000
arguments:  # optional, if any args must be submitted
    - arg1
    - arg2
upgradeable: True
readable: False
payable: False
payable_by_sc: False
```

### Contract Call Step

This step is used to call the endpoint of a contract.

```yaml
type: ContractCall
sender: alice
contract-id: my_first_sc
endpoint: myEndpoint
gas_limit: 60000000
arguments:  # optional, if any args must be submitted
  - arg1
value: 0  # optional, amount of egld to send
esdt_transfers:  # optional, esdt transfer to make
  - token_identifier: ALICE-123456
    amount: 58411548
    nonce: 0  # 0 for ESDT
  - token_identifier: LKMEX-e45d41
    amount: 848491898
    nonce: 721
```

### Contract Query Step

This step is used to fetch some data from a contract and save it locally for later use.
For example to fetch the identifier of a token newly created by a contract.

```yaml
type: ContractQuery
contract_id: my_first_sc
endpoint: getTokenAmounts
arguments:
  - TokenIdentifier1
  - TokenIdentifier2
expected_results:
  - save_key: TokenIdentifierAmount1
    result_type: number
  - save_key: TokenIdentifierAmount2
    result_type: number
print_results: False
```

Currently allowed values for `result_type`: [`number`, `str`]

### Loop Step

This steps allows to run a set of steps for a given number of times.
A loop variable is created and can be used as an arguments for the steps inside the loop.

```yaml
# This loop step retrieve the sft tokens with a nonce between 1 and 100.
# The loop variable is used to check and retrieve the amount of each nonce.
type: Loop
var_name: LOOP_VAR
var_start: 1
var_end: 100
steps:
  - type: ContractQuery
    contract_id: my_first_sc
    endpoint: getSftAmount
    arguments:
      - TokenIdentifier4
      - $LOOP_VAR  # nonce
    expected_results:
      - save_key: TokenIdentifier4Amount
        result_type: number
  
  - type: ContractCall
    sender: alice
    contract_id: my_first_sc
    endpoint: RetrieveSft
    gas_limit: 60000000
    arguments:
      - TokenIdentifier4
      - $LOOP_VAR  # nonce
      - "%my_first_sc%TokenIdentifier4Amount%"  # result of the query
    check_for_errors: False
```

Instead of using `var_start` and `var_end` for the loop variable, a custom list of values can be provided with the keyword `var_list`.
