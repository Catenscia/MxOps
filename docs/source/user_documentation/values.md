# Smart Values

To be as dynamic as possible, MxOps allows runtime/lazy evaluation of variables. This means that you can specify a generic argument or even compose a variable name and its actual value will change depending on the current state of the scenario.

## Base Syntax for Simple Smart Values

Simple smart values are specified with two parts:

`"<symbol><value_key>"`


for example:

- `"$MY_VAR"`
- `"&MY_VAR"`
- `"%contract_id.my_amount"`
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

The values saved within a scenario can be more complex and in particular they can have an infinite nested length, allowing you to store complex data
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

Data saved within a scenario are split into three categories: contract data, token data and everything else. A value attached to a contract or a token will always have its value key begins by the `contract_id` or the `token_name`. In addition, when you deploy a contract or a token, some values will already be available in the `Scenario data`.

Some examples of value key for data saved under a token or a contract:

| Value Key                    | Description                                             |
|------------------------------|---------------------------------------------------------|
| "contract-id.address"        | Address of the deployed contract                        |
| "contract-id.key_1.key_2[0]" | Anything that you decided to saved under this value key |
| "token-name.identifier"      | Token identifier of the issued token                    |
| "token-name.ticker"          | Ticker of the issued token                              |
| "token-name.key_1.key_2[5]"  | Anything that you decided to saved under this value key |
  
### Edge Cases

#### Loop variable

For a `Loop Step`, the loop variable is supplied through the current MxOps Scenario and so the `%` symbol should be used.

See examples in the [Loop Step section](loop_step_target).

#### Account Address

When MxOps knows that the provided value should be converted to an address, for example to specify the receiver of a transaction, the user can simply write the name of the account and MxOps will automatically translate it.
However, there are some ambiguous cases where an argument provided by a user could be a raw string (ex: "account_id") or the address represented by this string (ex: "erd...").
To avoid these confusions, a user can force MxOps to fetch the address of an account by using the syntax `%account_id.address`.


## Formula

Another symbol available with MxOps is the `=` symbol:

`"=<expression>"`

for example:

- `"=1+1"`
- `"=10**18"`
- `"=15648 // 7"`
- `"=randint(1, 5)"`

### Operators

MxOps will evaluate the expression as a python instruction and assign the obtained result to the value. Only a limited set of operators are allowed.


| Operator | Description                                                                     |
|----------|---------------------------------------------------------------------------------|
| +        | add two things. x + y 1 + 1 -> 2                                                |
| -        | subtract two things x - y 100 - 1 -> 99                                         |
| /        | divide one thing by another x / y 100/10 -> 10                                  |
| *        | multiple one thing by another x * y 10 * 10 -> 100                              |
| **       | 'to the power of' x**y 2 ** 10 -> 1024                                          |
| %        | modulus. (remainder) x % y 15 % 4 -> 3                                          |
| ==       | equals x == y 15 == 4 -> False                                                  |
| <        | Less than. x < y 1 < 4 -> True                                                  |
| >        | Greater than. x > y 1 > 4 -> False                                              |
| <=       | Less than or Equal to. x <= y 1 < 4 -> True                                     |
| >=       | Greater or Equal to x >= 21 1 >= 4 -> False                                     |
| >>       | "Right shift" the number. 100 >> 2 -> 25                                        |
| <<       | "Left shift" the number. 100 << 2 -> 400                                        |
| in       | is something contained within something else. "spam" in "my breakfast" -> False |
| ^        | "bitwise exclusive OR" (xor) 62 ^ 20 -> 42                                      |
| \|       | "bitwise OR" 8 \| 34 -> 42                                                      |
| &        | "bitwise AND" 100 & 63 -> 36                                                    |
| ~        | "bitwise invert" ~ -43 -> 42                                                    |

### Functions

MxOps also set at your disposal some useful functions


| Function | Description                                                                                                                                   | Example                        |
|----------|-----------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------|
| int      | convert to integer                                                                                                                            | `"=int('789')"`                |
| str      | convert to string                                                                                                                             | `"=str(12)"`                   |
| float    | convert to float                                                                                                                              | `"=float('1.2')"`              |
| rand     | generate a random number between 0 and 1, see [documentation](https://numpy.org/doc/stable/reference/random/generated/numpy.random.rand.html) | `"=rand()"`                    |
| randint  | generate a random integer, see [documentation](https://numpy.org/doc/stable/reference/random/generated/numpy.random.randint.html)             | `"=randint(1,5)"`              |
| choice   | pick at random a value, see [documentation](https://numpy.org/doc/stable/reference/random/generated/numpy.random.choice.html)                 | `"=choice(['alice', 'blob'])"` |


## Composability and Complex Smart Values

To add more flexibility, MxOps also handle variables composability, meaning that you mix up several type of smart values or even make reference to variables using other variables. To help MxOps differentiate variables, brackets `{}` must be used.

For example, if a user wanted to create 10 tokens with the names `Token1` to `Token10`, he could write the token name in the issuance step as `Token%{loop_var}` with `loop_var` going from 1 to 11 (excluded). (See [Loop Step section](loop_step_target) for more details).

Or if you want to add two values saved within MxOps, you could use `={%{value_1} + %{value_2}}`.

### Examples

This section exposes many examples, to give you an idea on what is possible with composition, but basically you can go pretty cray on variable composition. The only limits is that you have to respect the symbols and brackets syntax. 

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
"TOKEN_DECIMAL": "18" # (don't forget that environnement variables are strings)
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
        "code_hash": "5ce403a4f73701481cc15b2378cdc5bce3e35fa215815aa5eb9104d9f7ab2451",
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

The column `User Input` shows what the user could have written in a yaml scene file, the column `Composition Result` show the input transformed if any composition was used and the the column `Value` show the value that MxOps would have used, base the the context data defined above.


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
| "={int(%{my_dict.key1})}"                            | "={int('1')}"             | 1                                                                |
| "%{${OWNER_NAME}_%{suffix}.identifier}"              | "%{bob_token.identifier}" | "BOBT-123456"                                                    |
| "={int(%{my_dict.key1}) // %{my_dict.key2}}"         | "={int(1) // 2})"         | 0                                                                |

</div>
