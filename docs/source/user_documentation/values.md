# Values

To be as dynamic as possible, MxOps allows runtime evaluation of variables. This means that you can specify a generic argument and its actual value will change depending on the current state.

## Syntax

Values are specified with three parts, the last one being optional:

`"<symbol><value_key>[:<return_type>]"`


for example:

- `"$MY_VAR:int"`
- `"&MY_VAR:str"`
- `"%contract_id.my_amount:int"`
- `"%contract_id.my_amount"`

### Symbol

The symbol is used to indicate which data source to use.

| Symbol | Source                      |
|--------|-----------------------------|
| &      | MxOps configuration file    |
| $      | Environment variable        |
| %      | Scenario data               |

### Value Key

#### Configuration and Environment Variables

For the configuration and the environment variables, the value key is simply the name of the variable, for example: `"MY_CONSTANT"` or `"BASE_ISSUING_COST"`.

#### Scenario Data

The values saved within a `Scenario` can be more complex and in particular they can have an infinite nested length, allowing you to store complex data
while keeping things clean. To access the value, you simply write the full path of the value with a `.<key_name>` or `[<index>]` depending if the current element is a dictionary of a list.

For example, given the data below

```json
{
    "key_1": {
        "key_2": [
            {"data": "value_1"},
            "value_2"
        ],
        "key_3": "value_3"
    },
    "key_4": "value_4"
}
```

we can access the different values like this:

| value key             | value fetched |
|-----------------------|---------------|
| "key_1.key_2[0].data" | "value_1"     |
| "key_1.key_2[1]"      | "value_2"     |
| "key_1.key_3"         | "value_3"     |
| "key_4"               | "value_4"     |

Data saved within a `Scenario` are split into three categories: contract data, token data and everything else. A value attached to a contract or a token will always have its value key begins by the `contract_id` or the `token_name`. In addition, when you deploy a contract or a token, some values will already be available in the `Scenario data`. Some examples of value key for data saved under a token or a contract:

| Value Key                    | Description                                             |
|------------------------------|---------------------------------------------------------|
| "contract-id.address"        | Address of the deployed contract                        |
| "contract-id.key_1.key_2[0]" | Anything that you decided to saved under this value key |
| "token-name.identifier"      | Token identifier of the issued token                    |
| "token-name.ticker"          | Ticker of the issued token                              |
| "token-name.key_1.key_2[5]"  | Anything that you decided to saved under this value key |

### Return Type

For now, only two return types are supported:

- `int`
- `str`

If not specified, the value will be returned as it is saved.

```{warning}
Keep in mind that environment and configuration variables are always saved as strings.
```
  
## Edge Cases

### Loop variable

For a `Loop Step`, the loop variable is supplied through the environment and so the `%` symbol should be used.

See example in the [Loop Step section](loop_step_target).

### Account Address

To reference as an argument the address of an account specified in the `accounts` field of a `Scene`, one must use the following syntax: `[account_name]`.
