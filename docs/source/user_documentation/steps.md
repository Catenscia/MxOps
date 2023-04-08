# Steps

In `MxOps`, any action to be executed is called a `Step`.
In other words, a `Scene` contains a series of `Steps` that tells what `MxOps` should do.

Several type of `Steps` exists, to allow users to easily construct complex `Scenes`.
If you feel something is missing, please make a suggestion in the [github](https://github.com/Catenscia/MxOps/discussions/categories/ideas)!

## Contract Deploy Step

This `Step` is used to deploy a contract. The address of the new contract will be
saved in the `Scenario` (specified at execution time) under the provided id to allow future interactions.

```yaml
type: ContractDeploy
sender: bob
wasm_path: "path/to/wasm"
contract_id: my_first_sc
gas_limit: 1584000
arguments:  # optional, if any args must be submitted
    - 100
upgradeable: True
readable: False
payable: False
payable_by_sc: True
```

## Contract Call Step

This `Step` is used to call the endpoint of a deployed contract.

```yaml
type: ContractCall
sender: alice
contract-id: my_first_sc
endpoint: myEndpoint
gas_limit: 60000000
arguments:  # optional, args of the endpoint
  - arg1
value: 0  # optional, amount of eGLD to send
esdt_transfers:  # optional, ESDTs to send
  - token_identifier: ALICE-123456
    amount: 58411548
    nonce: 0  # 0 for fungible ESDT
  - token_identifier: LKMEX-e45d41
    amount: 848491898
    nonce: 721
checks:  # optional, by default it will contain a transaction success check
  - type: Success  
```

To get more information on the `checks` attribute, heads to the {doc}`checks` section.

## Contract Query Step

This `Step` is used to fetch some data from a contract and save it locally for later use in the `Scenario` (specified at execution time).
For example to fetch the identifier of a token created by a contract and stored in a `FungibleTokenMapper` with a view set up as `getEsdtIdentifier`.

```yaml
type: ContractQuery
contract: my_first_sc
endpoint: getEsdtIdentifier
arguments: []
expected_results:  # list of results excpected from the query output
  - save_key: EsdtIdentifier
    result_type: str
print_results: False  # if the query results should be printed in the console
```

Currently allowed values for `result_type`: [`number`, `str`]

(loop_step_target)=

## Loop Step

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
    contract: my_first_sc
    endpoint: getSftAmount
    arguments:
      - TokenIdentifier4
      - $LOOP_VAR  # nonce
    expected_results:
      - save_key: TokenIdentifier4Amount
        result_type: number
  
  - type: ContractCall
    sender: alice
    contract: my_first_sc
    endpoint: RetrieveSft
    gas_limit: 60000000
    arguments:
      - TokenIdentifier4
      - $LOOP_VAR  # nonce
      - "%my_first_sc%TokenIdentifier4Amount%"  # result of the query
    check_for_errors: False
```

Instead of using `var_start` and `var_end` for the loop variable, a custom list of values can be provided with the keyword `var_list` like below.

```yaml
type: Loop
var_name: LOOP_VAR
var_list: [1, 5, 78, 1566]
steps:
    [...]
```

You will notice that some symbols are used in the arguments of the above `ContractCall`. These are here to dynamically fetch values from different sources.
Heads up to the {doc}`values` section for more information.
