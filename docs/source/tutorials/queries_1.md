# Queries 1

This tutorial will showcase the following topics:

- Smart-contract queries
- Scenario data
- Smart values

The entire source code can be find in the MxOps [github](https://github.com/Catenscia/MxOps/tree/main/examples)

## Context

Let's say that we want to fetch some data from a smart-contract, either for informative purposes or because we will reuse it later on in. To do that we will execute queries, which will call read-only functions (also called views) on the targeted smart-contracts. It is always recommended to use the ABI of the contract you are going to interact with, as the ABI provided the definition of what views are available, how to use them and how the process the resulting data.

For our tutorial, we will take a look at the [mainnet swap contract of OneDex](https://explorer.multiversx.com/accounts/erd1qqqqqqqqqqqqqpgqqz6vp9y50ep867vnr296mqf3dduh6guvmvlsu3sujc), we will call it `onedex-swap` and we will try to get information on the current state of the pair pool ONE/WEGLD.

A second tutorial, [queries 2](queries_2), will go one step further and show how to make more complex queries and manipulate the received data.

## Prerequisites

You will need to have the following installed:

- MxOps: [installation steps](../getting_started/introduction)

## Tutorial plan

1. ABI download
2. Simple state query
3. theoretical price estimation
4. Swap estimation

To prepare for the tutorial, create a new folder

```bash
mkdir queries_tutorial
cd queries_tutorial
export MXOPS_SOURCE_BRANCH=main
```

## ABI Download

The first thing we need is the ABI of the `onedex-swap` contract. You can download it from using the command below:

```bash
mkdir data
curl https://raw.githubusercontent.com/Catenscia/MxOps/refs/heads/${MXOPS_SOURCE_BRANCH}/examples/queries/data/onedex-sc.abi.json > data/onedex-sc.abi.json
```

## Simple State Query

We want to query the state of a single pool, namely the pool ONE/WEGLD which has the id 9 on Onedex.
First create a new scene file:

```bash
mkdir mxops_scenes
touch mxops_scenes/single_pair_queries.yaml
```

### Network and Account

In our use-case, we want to interact with the mainnet, so we will add this to the beginning of the scene:

```yaml
allowed_networks:
  - mainnet
```

```{note}
By default, for security measure, scenes can be executed on all networks *except* mainnet. This is why we have to specify the allowed networks in our tutorial.
```

Then, we will declare the `onedex-swap` contract by giving it an account id and by providing the path to the abi file we downloaded previously:

```yaml
accounts:
  - account_id: onedex-swap
    address: erd1qqqqqqqqqqqqqpgqqz6vp9y50ep867vnr296mqf3dduh6guvmvlsu3sujc
    abi_path: ./abis/onedex-sc.abi.json
```

### View

If you look at the ABI file, you will see the following definition of the endpoint `viewPair`:

```json
{
    "name": "viewPair",
    "mutability": "readonly",
    "inputs": [
        {
            "name": "pair_id",
            "type": "u32"
        }
    ],
    "outputs": [
        {
            "type": "Pair"
        }
    ]
}
```

This is the endpoint that interests us, it returns a custom `Pair` structure, of which you can also find the definition in the ABI file. As we are providing the ABI, MxOps will be able to automatically decode the output data into this `Pair` structure.

To query the pair n°9 of the `onedex-swap` contract, add the following to your scene:

```yaml
steps:

  - type: ContractQuery
    contract: onedex-swap
    endpoint: viewPair
    arguments:
      - 9
    results_save_keys:
      - pair_9
```

We save the result (a `Pair` structure) into the key `onedex-swap.pair_9`. This will make us able to reuse this data.

### Full Scene

Your scene `mxops_scenes/single_pair_queries.yaml` should look like this:

```yaml
allowed_networks:
  - mainnet

accounts:
  - account_id: onedex-swap
    address: erd1qqqqqqqqqqqqqpgqqz6vp9y50ep867vnr296mqf3dduh6guvmvlsu3sujc
    abi_path: ./data/onedex-sc.abi.json

steps:

  - type: ContractQuery
    contract: onedex-swap
    endpoint: viewPair
    arguments:
      - 9
    results_save_keys:
      - pair_9

```

To execute it, use the following command:

```bash
mxops execute -n mainnet -s queries_tutorial mxops_scenes/single_pair_queries.yaml
```

```{dropdown} Command results
:class-title: normal-title
:color: light

```bash
[2025-04-02 15:12:38,622 INFO] MxOps  Copyright (C) 2025  Catenscia
This program comes with ABSOLUTELY NO WARRANTY [general in main_cli.py:65]
[2025-04-02 15:12:38,640 INFO] scenario queries_tutorial loaded for network mainnet [data in execution_data.py:836]
[2025-04-02 15:12:38,640 INFO] Executing scene mxops_scenes/single_pair_queries.yaml [execution in scene.py:148]
[2025-04-02 15:12:38,665 INFO] Query viewPair on erd1qqqqqqqqqqqqqpgqqz6vp9y50ep867vnr296mqf3dduh6guvmvlsu3sujc (onedex-swap) [execution in smart_contract.py:362]
[2025-04-02 15:12:38,808 INFO] Query results: {
    "pair_9": {
        "pair_id": 9,
        "state": {
            "__discriminant__": 1,
            "__name__": "Active"
        },
        "enabled": true,
        "owner": "erd1xkflzkx3hp52szy26zh9m5ts3v3j4dxhqkpxzj9npzp7wyp6qeysfpqz2m",
        "first_token_id": "ONE-f9954f",
        "second_token_id": "WEGLD-bd4d79",
        "lp_token_id": "ONEWEGLD-892244",
        "lp_token_decimal": 18,
        "first_token_reserve": 1495664529430316346685003,
        "second_token_reserve": 4450294287790899643561,
        "lp_token_supply": 1304000317043535522230,
        "lp_token_roles_are_set": true,
        "unkown": 0,
        "fees": 100
    }
} [execution in smart_contract.py:390]
```

### Saved Data

You can use the the command `mxops data get` to play around with the values saved by MxOps. Try to use it to recover some data about the pair n°9.

Examples

```bash
mxops data get -n mainnet -s queries_tutorial "%onedex-swap.pair_9.lp_token_id"
```

```{dropdown} Command results
:class-title: normal-title
:color: light

```bash
[2025-04-02 15:20:39,679 INFO] MxOps  Copyright (C) 2025  Catenscia
This program comes with ABSOLUTELY NO WARRANTY [general in main_cli.py:65]
[2025-04-02 15:20:39,697 INFO] scenario queries_tutorial loaded for network mainnet [data in execution_data.py:836]
ONEWEGLD-892244
```

```bash
mxops data get -n mainnet -s queries_tutorial "Pair 9 LP has a supply of ={%{onedex-swap.pair_9.lp_token_supply} / 10**%{onedex-swap.pair_9.lp_token_decimal}} %{onedex-swap.pair_9.lp_token_id}"
```

```{dropdown} Command results
:class-title: normal-title
:color: light

```bash
[2025-04-02 15:26:02,515 INFO] MxOps  Copyright (C) 2025  Catenscia
This program comes with ABSOLUTELY NO WARRANTY [general in main_cli.py:65]
[2025-04-02 15:26:02,532 INFO] scenario queries_tutorial loaded for network mainnet [data in execution_data.py:836]
Pair 9 LP has a supply of 1304.000317043535522230 ONEWEGLD-892244
```

## Price Estimation

We managed to get the current state of the pool ONE/WEGLD on OneDex. Using this data, we are going to perform some calculation: we will compute the current theoretical price of ONE versus WEGLD.

This theoretical price is simply the ratio between the WEGLD reserve and the ONE reserve of the pool and we already have this data thanks to the previous query.
To compute the theoretical price with MxOps, add the following to the scene:

```yaml
  - type: SetVars
    variables:
      one_reserve: "%onedex-swap.pair_9.first_token_reserve"
      wegld_reserve: "%onedex-swap.pair_9.second_token_reserve"
      pair_9_th_price: "={%{wegld_reserve} / %{one_reserve}}"
```

This will create variables and most importantly, compute the theoretical price of ONE versus WEGLD and store it under the key `pair_9_th_price`.

## Swap estimation

To be more complete, we will compare the theoretical price we just obtained to the actual amount of WEGLD we would get if we where to swap 1 ONE for WEGLD. For that, we are going to use the view `getAmountOut` of the contract `onedex-swap`:

```json
{
    "name": "getAmountOut",
    "mutability": "readonly",
    "inputs": [
        {
            "name": "token_in",
            "type": "TokenIdentifier"
        },
        {
            "name": "token_out",
            "type": "TokenIdentifier"
        },
        {
            "name": "amount_in",
            "type": "BigUint"
        }
    ],
    "outputs": [
        {
            "type": "BigUint"
        }
    ]
}
```

To call it within MxOps, add this step to your scene:

```yaml
  - type: ContractQuery
    contract: onedex-swap
    endpoint: getAmountOut
    arguments:
      - "%onedex-swap.pair_9.first_token_id"  # ONE -> token in
      - "%onedex-swap.pair_9.second_token_id"  # WEGLD -> token out
      - "=10**18" # -> 1 ONE (18 decimals)
    results_save_keys:
      - pair_9_amount_out
```

Lastly, to make it easier to compare to the theoretical price, we will compute the output amount as a float by dividing the result by 10**18 (ONE token has 18 decimals):

```yaml
  - type: SetVars
    variables:
      pair_9_float_amount_out: "={%{onedex-swap.pair_9_amount_out} / 10**18}"
```

## Final Scene

Your scene `mxops_scenes/single_pair_queries.yaml` should look like this:

```yaml
allowed_networks:
  - mainnet

accounts:
  - account_id: onedex-swap
    address: erd1qqqqqqqqqqqqqpgqqz6vp9y50ep867vnr296mqf3dduh6guvmvlsu3sujc
    abi_path: ./data/onedex-sc.abi.json

steps:

  - type: ContractQuery
    contract: onedex-swap
    endpoint: viewPair
    arguments:
      - 9
    results_save_keys:
      - pair_9

  - type: SetVars
    variables:
      one_reserve: "%onedex-swap.pair_9.first_token_reserve"
      wegld_reserve: "%onedex-swap.pair_9.second_token_reserve"
      pair_9_th_price: "={%{wegld_reserve} / %{one_reserve}}"

  - type: ContractQuery
    contract: onedex-swap
    endpoint: getAmountOut
    arguments:
      - "%onedex-swap.pair_9.first_token_id"
      - "%onedex-swap.pair_9.second_token_id"
      - "=10**18"
    results_save_keys:
      - pair_9_amount_out
  
  - type: SetVars
    variables:
      pair_9_float_amount_out: "={%{onedex-swap.pair_9_amount_out} / 10**18}"

```

To execute it, use the following command:

```bash
mxops execute -n mainnet -s queries_tutorial mxops_scenes/single_pair_queries.yaml
```

```{dropdown} Command results
:class-title: normal-title
:color: light

```bash
[2025-04-03 16:04:09,064 INFO] MxOps  Copyright (C) 2025  Catenscia
This program comes with ABSOLUTELY NO WARRANTY [general in main_cli.py:65]
[2025-04-03 16:04:09,082 INFO] scenario queries_tutorial loaded for network mainnet [data in execution_data.py:836]
[2025-04-03 16:04:09,083 INFO] Executing scene mxops_scenes/single_pair_queries.yaml [execution in scene.py:148]
[2025-04-03 16:04:09,098 INFO] Query viewPair on erd1qqqqqqqqqqqqqpgqqz6vp9y50ep867vnr296mqf3dduh6guvmvlsu3sujc (onedex-swap) [execution in smart_contract.py:362]
[2025-04-03 16:04:09,208 INFO] Query results: {
    "pair_9": {
        "pair_id": 9,
        "state": {
            "__discriminant__": 1,
            "__name__": "Active"
        },
        "enabled": true,
        "owner": "erd1xkflzkx3hp52szy26zh9m5ts3v3j4dxhqkpxzj9npzp7wyp6qeysfpqz2m",
        "first_token_id": "ONE-f9954f",
        "second_token_id": "WEGLD-bd4d79",
        "lp_token_id": "ONEWEGLD-892244",
        "lp_token_decimal": 18,
        "first_token_reserve": 1515337284792026638369995,
        "second_token_reserve": 4338610389278931476333,
        "lp_token_supply": 1295607106382727806181,
        "lp_token_roles_are_set": true,
        "unkown": 0,
        "fees": 100
    }
} [execution in smart_contract.py:390]
[2025-04-03 16:04:09,220 INFO] Setting variable `one_reserve` with the value `1515337284792026638369995` [execution in msc.py:137]
[2025-04-03 16:04:09,221 INFO] Setting variable `wegld_reserve` with the value `4338610389278931476333` [execution in msc.py:137]
[2025-04-03 16:04:09,224 INFO] Setting variable `pair_9_th_price` with the value `0.002863131814165311` [execution in msc.py:137]
[2025-04-03 16:04:09,237 INFO] Query getAmountOut on erd1qqqqqqqqqqqqqpgqqz6vp9y50ep867vnr296mqf3dduh6guvmvlsu3sujc (onedex-swap) [execution in smart_contract.py:362]
[2025-04-03 16:04:09,349 INFO] Query results: {
    "pair_9_amount_out": 2834498644189293
} [execution in smart_contract.py:390]
[2025-04-03 16:04:09,361 INFO] Setting variable `pair_9_float_amount_out` with the value `0.002834498644189293` [execution in msc.py:137]
```

We obtained a theoretical price of 1 ONE = 0.00286 WEGLD and a swap estimation of 1 ONE -> 0.00283 WEGLD.

```{note}
There will always be a difference between the theoretical price and a swap estimation as the swap estimation will take into account the fees and the price impact of the swap.
```

## 🏆 Conclusion

Congratulation, you learned how to do simple queries a third party contract using its ABI definition and how to inspect the resulting data.

A second tutorial will help you to take things a bit further, by making more complex queries and by doing more advanced data manipulation. To follow it, head over to the [queries 2 tutorial](queries_2).

Do not hesitate to [give us](../others/contact_us) your feedback on this tutorial 🙌