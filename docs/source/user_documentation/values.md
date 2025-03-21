(smart_values_target)=
# Values

To be as dynamic as possible, MxOps allows runtime evaluation of variables. This means that you can specify a generic argument or even compose a variable name and its actual value will change depending on the current state.

## Base Syntax

Values are specified with three parts, the last one being optional:

`"<symbol><value_key>[:<return_type>]"`


for example:

- `"$MY_VAR:int"`
- `"&MY_VAR:str"`
- `"%contract_id.my_amount:int"`
- `"%contract_id.my_amount"`

### Symbol

The symbol is there to indicate to MxOps which data source to use.

| Symbol | Source                      |
|--------|-----------------------------|
| &      | MxOps configuration file    |
| $      | Environment variable        |
| %      | MxOps Scenario data         |

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
    "key_4": "value_4",
    "key_5": {
        "key_6": ["alice", "bob"]
    }
}
```

we can access the different values like this:

| value key             | value fetched    |
|-----------------------|------------------|
| "key_1.key_2[0].data" | "value_1"        |
| "key_1.key_2[1]"      | "value_2"        |
| "key_1.key_3"         | "value_3"        |
| "key_4"               | "value_4"        |
| "key_5.key6"          | ["alice", "bob"] |

Data saved within a `Scenario` are split into three categories: contract data, token data and everything else. A value attached to a contract or a token will always have its value key begins by the `contract_id` or the `token_name`. In addition, when you deploy a contract or a token, some values will already be available in the `Scenario data`.

Some examples of value key for data saved under a token or a contract:

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

For a `Loop Step`, the loop variable is supplied through the current MxOps Scenario and so the `%` symbol should be used.

See examples in the [Loop Step section](loop_step_target).

### Account Address

When MxOps knows that the provided value should be converted to an address, for example to specify the receiver of a transaction, the user can simply write the name of the account and MxOps will automatically translate it.
However, there are some ambiguous cases where an argument provided by a user could be a raw string (ex: "account_id") or the address represented by this string (ex: "erd...").
To avoid these confusions, a user can force MxOps to fetch the address of an account by using the syntax `%account_id.address`.


## Composability

To add more flexibility, MxOps also handle variables composability, meaning that you can make reference to variables using other variables. To help MxOps differentiate variables, brackets `{}` must be used.

The syntax for composable variables is as below:

`"<symbol>{<value_key>[:<return_type>]}"`

For example, if a user wanted to create 10 tokens with the names `Token1` to `Token10`, he can write the token name as `Token%{loop_var}` with `loop_var` going from 1 to 11 (excluded). (See [Loop Step section](loop_step_target) for more details).

### Examples

This section exposes many examples, to give you an idea on what is possible with composition.

#### Context

For the examples below, let's setup some data context.

We have two accounts:

```
"alice": "erd1pqslfwszea4hrxdvluhr0v7dhgdfwv6ma70xef79vruwnl7uwkdsyg4xj3"
"bob": "erd1ddhla0htp9eknfjn628ut55qafcpxa9evxmps2aflq8ldgqq08esc3x3f8"
```

We have the following environment variables:

```
"OWNER_NAME": "bob"
"TOKEN_DECIMAL": "18" (don't forget that environnement variables are strings)
```

We have the following token data in the MxOps Scenario:

```json
"tokens_data": {
    "bob_token": {
        "saved_values": {},
        "name": "bob_token",
        "ticker": "BOBT",
        "identifier": "BOBT-123456",
        "type": "fungible"
    }
}
```

We have the following contract data in the MxOps Scenario:

```json
"contracts_data": {
    "my_test_contract": {
        "saved_values": {
            "query_result_1": [
                0,
                1,
                {
                    "2": "abc"
                }
            ],
            "my_key": 7458,
            "my_test_key": 4582
        },
        "contract_id": "my_test_contract",
        "address": "erd1qqqqqqqqqqqqqpgqdmq43snzxutandvqefxgj89r6fh528v9dwnswvgq9t",
        "serializer": null,
        "wasm_hash": "5ce403a4f73701481cc15b2378cdc5bce3e35fa215815aa5eb9104d9f7ab2451",
        "deploy_time": 1,
        "last_upgrade_time": 1
    }
}
```

And at last, the following saved values in the MxOps Scenario:

```json
"saved_values": {
    "user": "alice",
    "suffix": "token",
    "my_list": [
        "item1",
        "item2",
        "item3",
        {
            "item4-key1": "e"
        }
    ],
    "my_dict": {
        "key1": "1",
        "key2": 2,
        "key3": [
            "x",
            "y",
            "z"
        ]
    }
}
```

#### Examples Table


<div id="ValuesExamplesTable">

The column `User Input` shows what the user could have written in a yaml `Scene` file, the column `Composition Result` show the input transformed if any composition was used and the the column `Value` show the value that MxOps would have used, base the the context data defined above.

| User Input                                           | Composition Result        | Value                                                            |
|------------------------------------------------------|---------------------------|------------------------------------------------------------------|
| "%user"                                              | "%user"                   | "alice"                                                          |
| "%{%{user}.address}"                                 | "%{alice.address}"        | "erd1pqslfwszea4hrxdvluhr0v7dhgdfwv6ma70xef79vruwnl7uwkdsyg4xj3" |
| "%%{user}.address"                                   | %alice.address            | "erd1pqslfwszea4hrxdvluhr0v7dhgdfwv6ma70xef79vruwnl7uwkdsyg4xj3" |
| "$OWNER_NAME"                                        | "$OWNER_NAME"             | "bob"                                                            |
| "%{${OWNER_NAME}.address}"                           | "%{bob.address}"          | "erd1ddhla0htp9eknfjn628ut55qafcpxa9evxmps2aflq8ldgqq08esc3x3f8" |
| "%my_list"                                           | "%my_list"                | ["item1", "item2", "item3", {"item4-key1": "e"}]                 |
| "%my_list[0]"                                        | "%my_list[0]"             | "item1"                                                          |
| "%{my_list[0]}b"                                     | "item1b"                  | "item1b"                                                         |
| "%{my_list[0]}%{my_list[1]}%{my_list[3].item4-key1}" | "item1item2e"             | "item1item2e"                                                    |
| "%my_dict.key1"                                      | "%my_dict.key1"           | "1"                                                              |
| "%my_dict.key1:int"                                  | "%my_dict.key1:int"       | 1                                                                |
| "%{${OWNER_NAME}_%{suffix}.identifier}"              | "%{bob_token.identifier}" |                           "BOBT-123456"                          |

</div>
