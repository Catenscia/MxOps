# Queries 2

This tutorial will showcase the following topics:

- Smart-contract queries
- Smart values
- Scenario data

The entire source code can be find in the MxOps [github](https://github.com/Catenscia/MxOps/tree/main/examples)

## Context

This tutorial reuse the same context as the [queries 1 tutorial](queries_1), so you need to follow and execute it before attempting this second tutorial.

## Prerequisites

You will need to have the following installed:

- MxOps: [installation steps](../getting_started/introduction)

You will need to have followed the first tutorial [queries 1](queries_1).
You can place yourself in the working directory of the previous tutorial or not, the only requirement is that the previous tutorial has been executed so that the data has been saved in the scenario `queries_tutorial`. Indeed, we will rely on the ABI and the account id we defined for the onedex contract in the previous tutorial.


## Batch State Queries

We have successfully fetched the data of one pool, but onedex has hundreds of them and we want to optimize our requests. For this we will use the endpoint `viewPairsPaginated`, which will allow us to fetch several pairs per query.

```json
{
    "name": "viewPairsPaginated",
    "mutability": "readonly",
    "inputs": [
        {
            "name": "from",
            "type": "u32"
        },
        {
            "name": "size",
            "type": "u32"
        }
    ],
    "outputs": [
        {
            "type": "variadic<Pair>",
            "multi_result": true
        }
    ]
}
```

Create a new scene:

```bash
touch mxops_scenes/all_pairs_queries.yaml
```

### Number of Pairs

First we are going to fetch the number of pairs on the `onedex-swap` contract, using the endpoint `getLastPairId`:

```json
{
  "docs": [
      "\\n     * Last Pair Id\\n     "
  ],
  "name": "getLastPairId",
  "mutability": "readonly",
  "inputs": [],
  "outputs": [
      {
          "type": "u32"
      }
  ]
}
```

```yaml
allowed_networks:
  - mainnet

steps:

  - type: ContractQuery
    contract: onedex-swap
    endpoint: getLastPairId
    results_save_keys:
      - last-pair-id
```

This number will be accessible with `%onedex-swap.last-pair-id`.

### Variables

We will define three variables:

- batch_size: the number of pairs to get per query
- n_queries: the number of queries required to cover all the pairs ids, this is computed using the last pair id and the batch size.
- valid_onedex_pair_ids: this is a list in which we will put the valid pairs ids that we fetched successfully. Indeed, some onedex pairs are invalid and the endpoint `viewPairsPaginated` doesn't return them.


```yaml
  - type: SetVars
    variables:
      batch_size: 50
      n_queries: ={ceil(%{onedex-swap.last_pair_id} / %{batch_size})}
      valid_onedex_pair_ids: []
```

### Loop

To loop through the all the pairs, we are going to use a [`LoopStep`](loop_step_target), in which we will:

1. fetch the pairs batch
2. save the fetched pairs batch in a practical way
3. wait a little to avoid hitting gateway limits

```yaml
  - type: Loop
    var_name: i_queries
    var_start: 0
    var_end: "%n_queries"
    steps:
      # fetch the pairs batch
      # TODO

      # assign each pair data to a key related to the pair id
      # TODO
      
      # Wait a little to avoid hitting rate limits on mainnet proxy
      # TODO
```

#### Pairs Batch

To query the batch of pairs, we need to provide to the endpoint `viewPairsPaginated` the arguments `from` and `size`. `size` is simply equal to the batch size, whereas `from` is the first pair id of the batch. This id can be computed using the batch size and the current number of the loop.

```yaml
      # fetch the pairs batch
      - type: ContractQuery
        contract: onedex-swap
        endpoint: viewPairsPaginated
        arguments:
          - "={%{batch_size} * %{i_queries}}"   # from
          - "%batch_size"                       # size
        log_results: False
        results_save_keys:
          - batch_results
```

The batch is temporarily saved under the key `onedex-swap.batch_results`.

#### Data Save

We could have saved each pairs batch, but it wouldn't be very practical if we wanted to access the pair n°456 for example, because we wouldn't know how to access it. (We could compute the batch number but not the index of that pair within the batch, as some pairs are skipped by onedex).

Instead, we are going to save every pair data under the key `onedex_pair_<pair_id>`. To be able to loop through all the pairs, we are going to put all the fetched pair ids into the list `valid_onedex_pair_ids`.

```yaml
      # assign each pair data to a key related to the pair id
      - type: Loop
        var_name: pair_data
        var_list: "%onedex-swap.batch_results"
        steps:
          - type: SetVars
            variables:
              "onedex_pair_%{pair_data.pair_id}": "%pair_data"
              "valid_onedex_pair_ids[={len(%{valid_onedex_pair_ids})}]": "%pair_data.pair_id"
```

Some explanations:

- we loop over the batch result to get the individual pair data
- we use this pair data to get the id of the current pair (`%{pair_data.pair_id}`)
- we save this pair data under the key `onedex_pair_%{pair_data.pair_id}`
- we add the pair id to the end of the list `valid_onedex_pair_ids`.

#### Wait

If you are using your own gateway infrastructure, you can skip this step. Otherwise, please always be gentle with the public infrastructures, as they are useful to all the community.

```yaml
      # Wait a little to avoid hitting rate limits on mainnet proxy
      - type: Wait
        for_seconds: 0.5
```

### Pairs Names

Lastly, we will give names to all the pools, which will be formatted like this: `<first_token_id>/<second_token_id>`. Each pool name will be inserted into the existing saved pair data (`ondex_pair_<pair_id>`).

```yaml
  # set names to all pools
  - type: Loop
    var_name: pair_id
    var_list: "%valid_onedex_pair_ids"
    steps: 
      - type: SetVars
        variables:
          "onedex_pair_%{pair_id}.pair_name": "%{onedex_pair_%{pair_id}.first_token_id}/%{onedex_pair_%{pair_id}.second_token_id}"
```

### Final Scene

Your scene `mxops_scenes/all_pairs_queries.yaml` should look like this:

```yaml
allowed_networks:
  - mainnet

steps:

  - type: ContractQuery
    contract: onedex-swap
    endpoint: getLastPairId
    results_save_keys:
      - last_pair_id
  

  - type: SetVars
    variables:
      batch_size: 50
      n_queries: ={ceil(%{onedex-swap.last_pair_id} / %{batch_size})}
      valid_onedex_pair_ids: []
  
  - type: Loop
    var_name: i_queries
    var_start: 0
    var_end: "%n_queries"
    steps:
      # fetch the pairs batch
      - type: ContractQuery
        contract: onedex-swap
        endpoint: viewPairsPaginated
        arguments:
          - "={%{batch_size} * %{i_queries}}"   # from
          - "%batch_size"                       # size
        log_results: False
        results_save_keys:
          - batch_results

      # assign each pair data to a key related to the pair id
      - type: Loop
        var_name: pair_data
        var_list: "%onedex-swap.batch_results"
        steps:
          - type: SetVars
            variables:
              "onedex_pair_%{pair_data.pair_id}": "%pair_data"
              "valid_onedex_pair_ids[={len(%{valid_onedex_pair_ids})}]": "%pair_data.pair_id"
      
      # Wait a little to avoid hitting rate limits on mainnet proxy
      - type: Wait
        for_seconds: 0.5
      
  # set names to all pools
  - type: Loop
    var_name: pair_id
    var_list: "%valid_onedex_pair_ids"
    steps: 
      - type: SetVars
        variables:
          "onedex_pair_%{pair_id}.pair_name": "%{onedex_pair_%{pair_id}.first_token_id}/%{onedex_pair_%{pair_id}.second_token_id}"
```

To execute the scene, use the command below:

```bash
mxops execute -n mainnet -s queries_tutorial mxops_scenes/all_pairs_queries.yaml
```

```{dropdown} Command results
:class-title: normal-title
:color: light

```bash
[2025-04-02 15:51:22,517 INFO] MxOps  Copyright (C) 2025  Catenscia
This program comes with ABSOLUTELY NO WARRANTY [general in main_cli.py:65]
[2025-04-02 15:51:22,534 INFO] scenario queries_tutorial loaded for network mainnet [data in execution_data.py:836]
[2025-04-02 15:51:22,535 INFO] Executing scene mxops_scenes/all_pairs_queries.yaml [execution in scene.py:148]
[2025-04-02 15:51:22,538 INFO] Query getLastPairId on erd1qqqqqqqqqqqqqpgqqz6vp9y50ep867vnr296mqf3dduh6guvmvlsu3sujc (onedex-swap) [execution in smart_contract.py:362]
[2025-04-02 15:51:22,647 INFO] Query results: {
    "last_pair_id": 947
} [execution in smart_contract.py:390]
[2025-04-02 15:51:22,659 INFO] Setting variable `batch_size` with the value `50` [execution in msc.py:135]
[2025-04-02 15:51:22,663 INFO] Setting variable `n_queries` with the value `19` [execution in msc.py:135]
[2025-04-02 15:51:22,663 INFO] Setting variable `valid_onedex_pair_ids` with the value `[]` [execution in msc.py:135]
[2025-04-02 15:51:22,677 INFO] Query viewPairsPaginated on erd1qqqqqqqqqqqqqpgqqz6vp9y50ep867vnr296mqf3dduh6guvmvlsu3sujc (onedex-swap) [execution in smart_contract.py:362]
[2025-04-02 15:51:22,837 INFO] Query successful [execution in smart_contract.py:392]
[2025-04-02 15:51:22,854 INFO] Setting variable `onedex_pair_1` with the value `{'pair_id': 1, 'state': {'__discriminant__': 1, '__name__': 'Active'}, 'enabled': True, 'owner': 'erd19wjjxty40r6356r5mzjf2fmg8we2gxzshltunntk5tg45pl35r7ql8yzym', 'first_token_id': 'ESTAR-461bab', 'second_token_id': 'WEGLD-bd4d79', 'lp_token_id': 'ESTARWEGLD-083383', 'lp_token_decimal': 18, 'first_token_reserve': 5778262593545844309096675, 'second_token_reserve': 25303833973033426692, 'lp_token_supply': 89825690509080200982, 'lp_token_roles_are_set': True, 'unkown': 0, 'fees': 100}` [execution in msc.py:135]
[2025-04-02 15:51:22,854 INFO] Setting variable `valid_onedex_pair_ids[0]` with the value `1` [execution in msc.py:135]
[2025-04-02 15:51:22,869 INFO] Setting variable `onedex_pair_2` with the value `{'pair_id': 2, 'state': {'__discriminant__': 1, '__name__': 'Active'}, 'enabled': True, 'owner': 'erd1rfs4pg224d2wmndmntvu2dhfhesmuda6m502vt5mfctn3wg7tu4sk6rtku', 'first_token_id': 'MPH-f8ea2b', 'second_token_id': 'WEGLD-bd4d79', 'lp_token_id': 'MPHWEGLD-3deb18', 'lp_token_decimal': 18, 'first_token_reserve': 69, 'second_token_reserve': 264612852228120072, 'lp_token_supply': 142391218207681836, 'lp_token_roles_are_set': True, 'unkown': 0, 'fees': 40}` [execution in msc.py:135]
[2025-04-02 15:51:22,869 INFO] Setting variable `valid_onedex_pair_ids[1]` with the value `2` [execution in msc.py:135]
....
[2025-04-02 15:51:44,058 INFO] Setting variable `onedex_pair_946` with the value `{'pair_id': 946, 'state': {'__discriminant__': 1, '__name__': 'Active'}, 'enabled': True, 'owner': 'erd1uyh8yg9lcgxvnjqfw69dm25d92tu0mhxrw78xjjh2vuzc6dm3m6qcjd44h', 'first_token_id': 'WOJAINU-2e01e4', 'second_token_id': 'RONE-bb2e69', 'lp_token_id': 'WOJAINRONE-065e77', 'lp_token_decimal': 18, 'first_token_reserve': 1855040518629608, 'second_token_reserve': 117703811376733612989409, 'lp_token_supply': 1987654321000000000, 'lp_token_roles_are_set': True, 'unkown': 0, 'fees': 40}` [execution in msc.py:135]
[2025-04-02 15:51:44,060 INFO] Setting variable `valid_onedex_pair_ids[717]` with the value `946` [execution in msc.py:135]
[2025-04-02 15:51:44,073 INFO] Setting variable `onedex_pair_947` with the value `{'pair_id': 947, 'state': {'__discriminant__': 1, '__name__': 'Active'}, 'enabled': True, 'owner': 'erd1qqqqqqqqqqqqqpgqx25ymvvmqmvuklnx3ty20lwq6mf6l7nmptzsfaa8ev', 'first_token_id': 'RDG-e413f1', 'second_token_id': 'ONE-f9954f', 'lp_token_id': 'RDFUN-778d75', 'lp_token_decimal': 18, 'first_token_reserve': 199900769047071311912546297, 'second_token_reserve': 3934058465311303128121, 'lp_token_supply': 3800000000000000000002, 'lp_token_roles_are_set': True, 'unkown': 0, 'fees': 100}` [execution in msc.py:135]
[2025-04-02 15:51:44,075 INFO] Setting variable `valid_onedex_pair_ids[718]` with the value `947` [execution in msc.py:135]
[2025-04-02 15:51:44,088 INFO] Waiting for 0.5 seconds [execution in msc.py:156]
[2025-04-02 15:51:44,607 INFO] Query viewPairsPaginated on erd1qqqqqqqqqqqqqpgqqz6vp9y50ep867vnr296mqf3dduh6guvmvlsu3sujc (onedex-swap) [execution in smart_contract.py:362]
[2025-04-02 15:51:44,840 INFO] Query successful [execution in smart_contract.py:392]
[2025-04-02 15:51:44,853 INFO] Waiting for 0.5 seconds [execution in msc.py:156]
[2025-04-02 15:51:47,761 INFO] Setting variable `onedex_pair_1.pair_name` with the value `ESTAR-461bab/WEGLD-bd4d79` [execution in msc.py:135]
[2025-04-02 15:51:47,774 INFO] Setting variable `onedex_pair_2.pair_name` with the value `MPH-f8ea2b/WEGLD-bd4d79` [execution in msc.py:135]
...
[2025-04-02 15:51:57,191 INFO] Setting variable `onedex_pair_946.pair_name` with the value `WOJAINU-2e01e4/RONE-bb2e69` [execution in msc.py:135]
[2025-04-02 15:51:57,205 INFO] Setting variable `onedex_pair_947.pair_name` with the value `RDG-e413f1/ONE-f9954f` [execution in msc.py:135]
```



As of today, the last pair id is 947, but how many valid pairs there are? We can find out with the command below:

```bash
mxops data get -n mainnet -s queries_tutorial "number valid onedex pairs: ={len(%{valid_onedex_pair_ids})}"
```

```{dropdown} Command results
:class-title: normal-title
:color: light

```bash
[2025-04-02 16:07:50,688 INFO] MxOps  Copyright (C) 2025  Catenscia
This program comes with ABSOLUTELY NO WARRANTY [general in main_cli.py:65]
[2025-04-02 16:07:50,705 INFO] scenario queries_tutorial loaded for network mainnet [data in execution_data.py:836]
number valid onedex pairs: 719
```

### Saved Data

As before, try playing with the command `mxops data get` to inspect the data that we managed to fetch.

## 🏆 Conclusion

Congratulation, you learned how to query a third party contract using its ABI definition and you learned to manipulate complex data with MxOps!

This will surely come handy for you project! Do not hesitate to [give us](../others/contact_us) your feedback on this tutorial 🙌