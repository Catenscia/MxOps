# Values

To be as dynamic as possible, MxOps allows runtime evaluation of variables. This means that you can specify a generic argument and its actual value will change depending on its current state.

## Syntax

Values are specified as below:

`"<symbol><name>:<type>"`

for example:

- `"$MY_VAR:int"`
- `"&MY_VAR:str"`
- `"%CONTRACT_ID%MY_VAR:int"`

### Symbol

The symbol is used to indicate which data source to use.

| Symbol | Source               |
|--------|----------------------|
| &      | MxOps config file    |
| $      | Environment variable |
| %      | Scenario data        |

### Type

For now, only two types are supported:

- `int`
- `str`
  
## Edge Cases

### Loop variable

For a `Loop Step`, the loop variable is supplied through the environment and so the `$` symbol should be used.

See example in the [Loop Step section](loop_step_target).

### Account Address

To reference the address of an account specified in the `accounts` field of a `Scene`, one must use the following syntx: `[account_name]`.
