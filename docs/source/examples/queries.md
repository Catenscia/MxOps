# Queries

MxOps is a great way to directly query data from smart-contracts. it offer a very simple way to retrieve the data, decode it and finally display or save the results.

(example_raw_query)=
## Raw

If you don't have the ABI file of the contract you are trying to interact with and you have no idea of the return type of the query, MxOps will simply print the raw data in several formats.

```yaml
allowed_networks:
    - mainnet

allowed_scenario:
    - .*

external_contracts:
  xexchange-wegld-usdc: erd1qqqqqqqqqqqqqpgqeel2kumf0r8ffyhth7pqdujjat9nx0862jpsg2pqaq

steps:

  - type: ContractQuery
    contract: xexchange-wegld-usdc
    endpoint: getReservesAndTotalSupply
    print_results: true
```

Printed results:
```bash
[
    {'base64': 'EUUHwqUftPcF0Q==', 'hex': '114507c2a51fb4f705d1', 'number': 81553614740729273714129},
    {'base64': 'BGwsS5OI', 'hex': '046c2c4b9388', 'number': 4862646129544},
    {'base64': 'CIc7gJxl', 'hex': '08873b809c65', 'number': 9376911891557}
]
```

Here, three results have been returned and each of them is display under three forms: base64, hex and number. Raw queries are useful when you are not sure what type of raw data is returned by a contract and you need to investigate the outputs under its raw form.

```{note}
Raw queries results cannot be saved as queries results by MxOps as their types is unknown. Once you have deciphered the outputs types, we recommend creating an ABI file or specifying the expected results types. Both methods are described further down.
```

(example_query_with_abi)=
## With ABI

If you have an ABI file at your disposal, we recommend specifying it to MxOps, as it is the simplest way of interacting with a contract. If you don't have it, you can always execute [raw queries](example_raw_query), infer the types and write yourself an ABI file.

```{note}
If you need help to decrypt your data, write the ABI or setup your `Scenes`, don't hesitate to [contact us](get_help)
```


```yaml
allowed_networks:
    - mainnet

allowed_scenario:
    - .*

external_contracts:
  onedex-swap: 
    address: erd1qqqqqqqqqqqqqpgqqz6vp9y50ep867vnr296mqf3dduh6guvmvlsu3sujc
    abi_path: ./abis/onedex-sc.abi.json

steps:

  - type: ContractQuery
    contract: onedex-swap
    endpoint: viewPair
    arguments:
      - 10
    print_results: true
```

Printed results:
```bash
[
    {
        "pair_id": 10,
        "state": {
            "name": "Active",
            "discriminant": 1,
            "values": null
        },
        "enabled": true,
        "owner": "erd1rfs4pg224d2wmndmntvu2dhfhesmuda6m502vt5mfctn3wg7tu4sk6rtku",
        "first_token_id": "MPH-f8ea2b",
        "second_token_id": "USDC-c76f1f",
        "lp_token_id": "MPHUSDC-777138",
        "lp_token_decimal": 18,
        "first_token_reserve": 16,
        "second_token_reserve": 1076937,
        "lp_token_supply": 393944771203191982,
        "lp_token_roles_are_set": true
    }
]
```

## With Results Types

If you don't have the ABI at your disposal and don't want to write one yourself, you can specify directly at the `Step` level the results you want to obtain. Here, we will take the first example with the [raw query](example_raw_query) while adding the results types this time:

```yaml
allowed_networks:
    - mainnet

allowed_scenario:
    - .*

external_contracts:
  xexchange-wegld-usdc: erd1qqqqqqqqqqqqqpgqeel2kumf0r8ffyhth7pqdujjat9nx0862jpsg2pqaq

steps:

  - type: ContractQuery
    contract: xexchange-wegld-usdc
    endpoint: getReservesAndTotalSupply
    print_results: true
    results_types:
      - type: BigUint
      - type: BigUint
      - type: BigUint
```

Printed results:
```bash
[
    81553614740729273714129,
    4862646129544,
    9376911891557
]
```