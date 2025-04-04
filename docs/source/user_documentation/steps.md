# Steps

In MxOps, any action to be executed is called a step.
In other words, a scene contains a list of steps that tell what MxOps should do.

Several type of steps exists, to allow users to easily construct complex scenes.
If you feel something is missing, please make a suggestion in the [github](https://github.com/Catenscia/MxOps/discussions/categories/ideas)!

## Transfer Step

This step is used to describe any king of transfer: native token, simple esdt, nft, ...

```yaml
type: Transfer
sender: bob
receiver: alice   # you can also directly write a bech32 address here
value: 7895651689  # optional, integer amount of EGLD to send
transfers:  # optional, any ESDT, NFT, SFT, MEta-ESDT transfers
  - identifier: "MYNFT-a123ec"
    nonce: 156
    amount: 1  
  - identifier: "WEGLD-abcdef"
    amount: 14894651698498  
```

```{note}
As of now, EGLD can not be sent at the same time as ESDTs, you have to choose between the two.
```

Egld transfer example:

```yaml
type: Transfer
sender: bob
receiver: alice
value: 1000000000000000000 # 1 EGLD
```

Multi ESDT transfer example:

```yaml
type: Transfer
sender: bob
receiver: alice
transfers:
  - identifier: "MYNFT-a123ec"
    nonce: 156
    amount: 1  
  - identifier: "WEGLD-abcdef"
    amount: 1000000000000000000  # 1 WEGLD  
```

```{tip}
If you are tired of writing token amounts with a lot of zeros, you can also write it like this: `amount: =10**18`. This will be parsed as a formula by MxOps and will be equivalent to 1 EGLD in our case. (Be careful with tokens that have a different number of decimals). See [smart-values](values) for more details.
```

## Contract Steps

### Contract Deploy Step

This step is used to deploy a contract. The address of the new contract will be
saved in the scenario (specified at execution time) under the provided id to allow future interactions.

```yaml
type: ContractDeploy
sender: bob
wasm_path: "path/to/wasm"
abi_path: "path/to/abi"  # optional but strongly recommended
contract_id: my_first_sc
gas_limit: 1584000
arguments: # optional, if any args must be submitted to the init function
  - 100
upgradeable: true
readable: false
payable: false
payable_by_sc: true
```

We strongly recommended to provide an ABI with the contract as this will allow MxOps to do the data encoding and decoding during queries and calls for you, even if the data is some complex or custom structure.

### Contract Upgrade Step

This step is used to upgrade a contract.

```yaml
type: ContractUpgrade
sender: bob
wasm_path: "path/to/upgraded_wasm"
abi_path: "path/to/abi"  # optional but strongly recommended
contract: my_first_sc
gas_limit: 1584000
arguments: # optional, if any args must be submitted to the upgrade function
  - 100
upgradeable: true
readable: false
payable: false
payable_by_sc: true
```

```{warning}
Be mindful of the difference in the argument name between the deploy and the update steps.

`contract_id` can only refer to a contract managed by MxOps whereas `contract` can be any contract. This means that you can upgrade a contract that has not been deployed by MxOps.
```

(contract_call_target)=
### Contract Call Step

This step is used to call the endpoint of a deployed contract.

```yaml
type: ContractCall
sender: alice
contract: my_first_sc
endpoint: myEndpoint
gas_limit: 60000000
arguments: # optional, args of the endpoint
  - arg1
value: 0 # optional, integer amount of eGLD to send
esdt_transfers: # optional, ESDTs to send
  - identifier: ALICE-123456
    amount: 58411548
  - identifier: LKMEX-e45d41
    amount: 848491898
    nonce: 721
results_save_keys: # optional, key(s) under which save the results of the call
  - call_result
log_results: true # optional, if the calls results should be printed in the console, default to true
checks: # optional, by default it will contain a transaction success check
  - type: Success
```

If you have provided an ABI with the contract, MxOps will be able to automatically encode the arguments for your call, even if they are complex structures. For more details on that, please head to the {doc}`serialization` section.
MxOps will also automatically decode the response of the call so that if you save the data, you can easily use it again by reference (see [smart values chapter](values)).


To get more information on the checks attribute, heads to the [transaction checks chapter](checks).
If you have provided an ABI with the contract, MxOps will be able to automatically encode the arguments for your endpoint call, even if they are complex structures. For more details on that, please head to the [serialization chapter](serialization).

(result_save_keys_target)=
#### About `results_save_keys`

There are several accepted types for `results_save_keys` which will indicated how you want to save the data. You can provided either a master key or some sub-keys or both. The master keys will point to the entire query response whereas sub-keys points to individual result of the queries.
You will find some examples below:

##### Results Save Keys Example 1

Query return type: `(BigUint, BigInt)`

Decoded query response: `[[123456, -7891011]]`

```{list-table}
:header-rows: 1

* - results_save_keys
  - Data saved within the scenario
* - ```yaml
    results_save_keys: master_key
    ```
  - ```json
    {
      "master_key": [[123456, -7891011]]
    }
    ```
* - ```yaml
    results_save_keys:
      master_key:
        - sub_key_1
    ```
  - ```json
    {
      "master_key": {
        "sub_key_1": [123456, -7891011]
      }
    }
    ```
* - ```yaml
    results_save_keys:
      - sub_key_1
    ```
  - ```json
    {
      "sub_key_1": [123456, -7891011]
    }
    ```
```



##### Results Save Keys Example 2

Query return type: `MultiValue2<u32, i8>`

Decoded query response: `[12, -1]`

```{list-table}
:header-rows: 1

* - results_save_keys
  - Data saved within the scenario
* - ```yaml
    results_save_keys: master_key
    ```
  - ```json
    {
      "master_key": [12, -1]
    }
    ```
* - ```yaml
    results_save_keys:
      master_key:
        - sub_key_1
        - sub_key_2
    ```
  - ```json
    {
      "master_key": {
        "sub_key_1": 12,
        "sub_key_2": -1
      }
    }
    ```
* - ```yaml
    results_save_keys:
      - sub_key_1
      - sub_key_2
    ```
  - ```json
    {
      "sub_key_1": 12,
      "sub_key_2": -1
    }
    ```
```


##### Results Save Keys Example 3

Query return type: `MultiValue2<u8, MyStruct<Self::Api>>`

Decoded query response: `[234, {"attribute_1": "WEGLD-abcdef", "attribute_2": 123456}]`


```{warning}
If you provide sub-keys, the number of sub-keys must exactly match the number of elements returned by the query response.
```

```{list-table}
:header-rows: 1

* - results_save_keys
  - Data saved within the scenario
* - ```yaml
    results_save_keys: master_key
    ```
  - ```json
    {
      "master_key": [
        234,
        {
            "attribute_1": "WEGLD_abcdef",
            "attribute_2": 123456
        }
      ]
    }
    ```
* - ```yaml
    results_save_keys:
      master_key:
        - sub_key_1
        - sub_key_2
    ```
  - ```json
    {
      "master_key": {
        "sub_key_1": 234,
        "sub_key_2": {
          "attribute_1": "WEGLD_abcdef",
          "attribute_2": 123456
        }
      }
    }
    ```
* - ```yaml
    results_save_keys:
      - sub_key_1
      - sub_key_2
    ```
  - ```json
    {
      "sub_key_1": 234,
      "sub_key_2": {
        "attribute_1": "WEGLD_abcdef",
        "attribute_2": 123456
      }
    }
    ```
```

(contract_query_target)=
### Contract Query Step

This step is used to fetch some data from a contract by calling one of its view.
In the example below, we want to fetch the identifier of a token created by a contract and stored in a `FungibleTokenMapper` with a view set up as `getEsdtIdentifier`.

```yaml
type: ContractQuery
contract: my_first_sc
endpoint: getEsdtIdentifier
arguments: []  # optional, if the view needs any arguments
results_save_keys: # optional, key(s) under which save the results of the query
  - EsdtIdentifier
log_results: true # optional, if the query results should be printed in the console, default to true
```

If you have provided an ABI with the contract, MxOps will be able to automatically encode the arguments for your query, even if they are complex structures. For more details on that, please head to the {doc}`serialization` section.
MxOps will also automatically decode the response of the query so that if you save the data, you can easily use it again by reference (see [smart values chapter](values)).

#### About `results_save_keys`

refer to the [previous section](result_save_keys_target).

(file_fuzzer_target)=
### File Fuzzer Step

This step is used to execute some fuzz testing. The parameters for the tests (queries or calls) are taken from a file.
At the moment, only yaml format is supported.

```yaml
type: FileFuzzer
contract: "my-contract-id"
file_path: "./path/to/my_fuzzer_parameters.yaml"
```

#### Yaml File Format

```yaml
parameters:
  - endpoint: my_endpoint  # query or call
    sender: bob  # name or bech32 of the sender of the tx (optional for query)
    gas_limit: 89984  # optional, only for calls
    value: 0  # optional, if any EGLD is to be sent with the call
    esdt_transfers:  # optional, if any esdt are to be sent with the call
      - identifier: TOKEN-abcdef
        amount: 120924
        nonce: 0  # optional, default to 0
    arguments:  # optional, argument to pass to the query/call as usual in MxOps
      - 12145
      - TOKEN-abcdef
    expected_outputs:  # optional, excepted output of the query or call
      - 12124115
    description: "test description"

  - endpoint: my_endpoint 
    ....
```

#### Considerations

At the moment, this step is a work in progress.

- esdt transfers happening within a transaction cannot be tested
- intentional error cannot be tested

(token_management_target)=
## Token Management Steps

### Fungible Token Steps

#### Issuance Step

This step is used to issue a new fungible token, and an initial supply of tokens will be sent to the issuer.

```yaml
type: FungibleIssue
sender: alice
token_name: MyToken # must be unique within a Scenario
token_ticker: MTK
initial_supply: 1000000000 # 1,000,000.000 MTK
num_decimals: 3
can_freeze: false # optional, defaults to false
can_wipe: false # optional, defaults to false
can_pause: false # optional, defaults to false
can_change_owner: false # optional, defaults to false
can_upgrade: false # optional, defaults to false
can_add_special_roles: false # optional, defaults to false
```

You can make a reference to this token in later steps using its name, for example to refer to the token identifier, just use `%MyToken.identifier`.

```{warning}
To avoid data collision within MxOps, `token_name` should be unique within a scenario and should not have a name identical to a `contract_id` in the same scenario.
```

#### Role Management Step

This step is used to set or unset roles for an address on a fungible token.

```yaml
type: ManageFungibleTokenRoles
sender: alice
token_identifier: MTK-abcdef
target: erd17jcn20jh2k868vg0mm7yh0trdd5mxpy4jzasaf2uraffpae0yrjsvu6txw
is_set: true # if false, this will unset the provided roles
roles: # choose one or several of the roles below
  - local_mint
  - local_burn
  - esdt_transfer_role
```

Details on the roles can be found [here](https://docs.multiversx.com/tokens/esdt-tokens/#setting-and-unsetting-special-roles).

#### Mint Step

This step is used to mint an additional supply for an already existing fungible token.

```yaml
type: FungibleMint
sender: alice
token_identifier: MTK-abcdef
amount: 100000000
```

### NFT, SFT and Meta Token Steps

Aside from the issuance steps, NFT, SFT and Meta tokens share common methods. The associated steps are listed here.

#### NFT Issuance Step

This step is used to issue a new non fungible token (NFT).

```yaml
type: NonFungibleIssue
sender: alice
token_name: MyNFT # must be unique within a Scenario
token_ticker: MNFT
can_freeze: false # optional, defaults to false
can_wipe: false # optional, defaults to false
can_pause: false # optional, defaults to false
can_change_owner: false # optional, defaults to false
can_upgrade: false # optional, defaults to false
can_add_special_roles: false # optional, defaults to false
can_transfer_nft_create_role: false # optional, defaults to false
```

You can make a reference to this token in later steps using its name, for example to refer to the token identifier, just use `%MyToken.identifier`.

```{warning}
To avoid data collision within MxOps, `token_name` should be unique within a scenario and should not have a name identical to a `contract_id` in the same scenario.
```

#### SFT Issuance Step

This step is used to issue a new semi fungible token (NFT).

```yaml
type: SemiFungibleIssue
sender: alice
token_name: MySFT # must be unique within a Scenario
token_ticker: MSFT
can_freeze: false # optional, defaults to false
can_wipe: false # optional, defaults to false
can_pause: false # optional, defaults to false
can_change_owner: false # optional, defaults to false
can_upgrade: false # optional, defaults to false
can_add_special_roles: false # optional, defaults to false
can_transfer_nft_create_role: false # optional, defaults to false
```

You can make a reference to this token in later steps using its name, for example to refer to the token identifier, just use `%MyToken.identifier`.

```{warning}
To avoid data collision within MxOps, `token_name` should be unique within a scenario and should not have a name identical to a `contract_id` in the same scenario.
```

#### Meta Issuance Step

This step is used to issue a new non fungible token (NFT).

```yaml
type: MetaIssue
sender: alice
token_name: MyMeta # must be unique within a Scenario
token_ticker: MMT
num_decimals: 3
can_freeze: false # optional, defaults to false
can_wipe: false # optional, defaults to false
can_pause: false # optional, defaults to false
can_change_owner: false # optional, defaults to false
can_upgrade: false # optional, defaults to false
can_add_special_roles: false # optional, defaults to false
can_transfer_nft_create_role: false # optional, defaults to false
```

You can make a reference to this token in later steps using its name, for example to refer to the token identifier, just use `%MyToken.identifier`.

```{warning}
To avoid data collision within MxOps, `token_name` should be unique within a scenario and should not have a name identical to a `contract_id` in the same scenario.
```

#### NFT Role Management Step

This step is used to set or unset roles for an address on a non fungible token.

```yaml
type: ManageNonFungibleTokenRoles
sender: alice
token_identifier: MNFT-abcdef
target: erd17jcn20jh2k868vg0mm7yh0trdd5mxpy4jzasaf2uraffpae0yrjsvu6txw
is_set: true # if false, this will unset the provided roles
roles: # choose one or several of the roles below
  - nft_create
  - nft_burn
  - nft_update_attributes
  - nft_add_uri
  - esdt_transfer_role
  - nft_update
  - esdt_modify_royalties
  - esdt_set_new_uri
  - esdt_modify_creator
  - nft_recreate

```

Details on the roles can be found [here](https://docs.multiversx.com/tokens/nft-tokens#roles).

#### SFT Role Management Step

This step is used to set or unset roles for an address on a semi fungible token.

```yaml
type: ManageSemiFungibleTokenRoles
sender: alice
token_identifier: MNFT-abcdef
target: erd17jcn20jh2k868vg0mm7yh0trdd5mxpy4jzasaf2uraffpae0yrjsvu6txw
is_set: true # if false, this will unset the provided roles
roles: # choose one or several of the roles below
  - nft_create
  - nft_burn
  - nft_add_quantity
  - esdt_transfer_role
  - nft_update
  - esdt_modify_royalties
  - esdt_set_new_uri
  - esdt_modify_creator
  - nft_recreate
```

Details on the roles can be found [here](https://docs.multiversx.com/tokens/nft-tokens#roles).

#### Meta Role Management Step

This step is used to set or unset roles for an address on a meta token.

```yaml
type: ManageMetaTokenRoles
sender: alice
token_identifier: META-abcdef
target: erd17jcn20jh2k868vg0mm7yh0trdd5mxpy4jzasaf2uraffpae0yrjsvu6txw
is_set: true # if false, this will unset the provided roles
roles: # choose one or several of the roles below
  - nft_create
  - nft_burn
  - nft_add_quantity
  - esdt_transfer_role
  - nft_update
  - esdt_modify_royalties
  - esdt_set_new_uri
  - esdt_modify_creator
  - nft_recreate
```

Details on the roles can be found [here](https://docs.multiversx.com/tokens/nft-tokens#roles).

#### Non Fungible Mint Step

This step is used to mint a new nonce for an already existing non fungible token.
It can be used for NFTs, SFTs and Meta tokens.

```yaml
type: NonFungibleMint
sender: alice
token_identifier: TOKE-abcdef
amount: 1 # must be 1 for NFT but any number for SFT and Meta
name: "Beautiful NFT" # optional
royalties: 750 # optional, here it is equals to 7.5%
hash: "00" # optional
attributes: "metadata:ipfsCID/song.json;tags:song,beautiful,music" # optional
uris: # optional
  - https://mypng.com/1
  - https://mysftjpg.com/1
```

You can find more information in the MultiversX documentation about [non fungible creation](https://docs.multiversx.com/tokens/nft-tokens#creation-of-an-nft) and [non fungible attributes](https://docs.multiversx.com/tokens/nft-tokens#nftsft-fields).

## Setup Steps

(generate_wallets_target)=
### Generate Wallets Step

This step allows you to generate new wallets. For now, only PEM wallets can be generated

```yaml
type: GenerateWallets
save_folder: ./my/wallets  # folder where to save the generated wallets
wallets: 10  # number of wallets to generate
shard: 1  # optional, to force the shard of the generated wallets
```

If you prefer to names you wallets, you can provide a list of names instead.

```yaml
type: GenerateWallets
save_folder: ./my/wallets  # folder where to save the generated wallets
wallets: ["alice", "bob"]  # generate two wallets named alice and bob
shard: 0  # optional, to force the shard of the generated wallets
```


(r3d4_faucet_target)=
### r3d4 Faucet Step

This step allows you use devnet and testnet faucet [r3d4](https://r3d4.fr/faucet).
This is a third party tool that is not managed by Catenscia, so the compatibility might break.

Some things to keep in mind:
- Respect the limits from r3d4 (1 claim per token per address per day)
- There may be some delays before you receive the funds
- Please don't abuse the faucet, it's a tool useful for a lot of people
- If you have to much funds, send them back to the faucet so that they can be reused
- The faucet only works for devnet and testnet

Example:

```yaml
type: R3D4Faucet
targets:
  - alice  # account name handeld by MxOps
  - erd1y3296u7m2v5653pddey3p7l5zacqmsgqc7vsu3w74p9jm2qp3tqqz950yl  # or direct bech32
```

Here, for each address, the maximum amount of EGLD (1 EGLD as of December 2024) will be requested.


(chain_simulator_faucet_target)=
### Chain Simulator Faucet Step

This step allows you to request EGLD on the chain-simulator. Unless you use tremendous amount of EGLD, you shouldn't run into any limit here.

```yaml
type: ChainSimulatorFaucet
amount: 1000000000000000000  # 1.0 EGLD
targets:
  - alice  # account name handeld by MxOps
  - erd1y3296u7m2v5653pddey3p7l5zacqmsgqc7vsu3w74p9jm2qp3tqqz950yl  # or direct bech32
```

(account_clone_target)=
### Account Clone Step

Exclusive to the chain simulator.
This step allows you to clone an account from another network (ex mainnet) and to import it to the chain simulator.
You can choose to clone, the code, the balance, the storage and the tokens of an account.

When cloning tokens, MxOps makes sure that the tokens are well defined in the network and you will be able to use them as if they were natively generated on the chain-simulator in the first place.

```yaml
type: AccountClone
address: my_mainnet_contract
source_network: mainnet
clone_balance: true  # optional, default to true
clone_code: true  # optional, default to true
clone_storage: true  # optional, default to true
clone_esdts: true  # optional, default to true
overwrite: true  # optional, default to true
overwrite: true  # optional, default to true
caching_period: "10 days"  # optional, default to 10 days
```

Account cloning can lead to huge data requests. If you are using the public proxy, please use a high caching period.
Currently, some clones will even fail because the storage of the account is too big. This will be fixed on the MultiversX side in the [bernard release](https://github.com/multiversx/mx-chain-go/pull/6547) by the core team.

## Miscellaneous Steps

(loop_step_target)=
### Loop Step

This step allows to run a set of steps in a loop.
A loop variable is created and can be used as an argument for the steps inside the loop.

```yaml
type: Loop
var_name: nonce
var_start: 1
var_end: 100
steps:

  # <do someting>

  # use the loop variable nonce to get the amount of SFT in a smart-contract
  # and save the amount under the key my_sft_bank.<token_identifier>_<nonce>_amount
  - type: ContractQuery
    contract: my_sft_bank
    endpoint: getSftAmount
    arguments:
      - "%sft_identifier"
      - "%nonce"
    results_save_keys:
      - "%{sft_identifier}_%{nonce}_amount"

  # <do something else>
```

Instead of using `var_start` and `var_end` for the loop variable, a custom list of values can be provided with the keyword `var_list` like below.

```yaml
type: Loop
var_name: i
var_list: [1, 5, 78, 1566]
steps: [...]
```

You will notice that the symbol `%` is used in the arguments of the above `ContractQuery` step. It is here to dynamically fetch the value of the loop variable from the scenario data. Heads up to the [smart values chapter](values) for more information.

(python_step_target)=
### Python Step

This step allows to execute a custom python function. You can execute whatever you want in the python function. This step is here to give you maximum flexibility, making MxOps suitable for all the needs of you project. Here are some basic use case for the python step:
  - complex calculation (results can be saved as MxOps or environment values)
  - complex query parsing
  - randomness generation
  - third party calls (databases, API ...)

For the function, the user can provide raw arguments or can use the MxOps values format.
The python function result can be saved as a scenario variable if the user desires it.

```{warning}
The results returned by the python function should always parsable by json, otherwise the data save will fail and the execution will stop.
```

```yaml
type: Python
module_path: ./folder/my_module.py
function: my_function
arguments:  # optional
  - arg1
  - "%my_contract.query_result"  # using MxOps value
keyword_arguments:  # optional
  key_1: value_1
  key_2: "$VALUE"  # using os env var
log_result: True  # optional
result_save_key: "my_result"  # optional, key under which save the function result
```

The above step will execute the function `my_function`, located at `./folder/my_module.py` that would look like this:
```python
def my_function(arg_1, arg2, key_1, key_2):
    # execute anything here
    return result
```

You can find examples of python steps in the [tutorial and example section](../tutorials/introduction).

```{warning}
MxOps is completely permissive and lets you do anything you want in the python step, including changing the behavior of MxOps itself. Test everything you do on chain-simulator, localnet and/or devnet before taking any action on mainnet.
```

### Scene Step

This step simply runs a scene or a folder of scenes. It can be used either to organize different executions or more importantly, to avoid copy pasting steps.
It is especially powerful if you combine it with [smart-values](values).

```yaml
type: Scene
path: ./integration_tests/setup_scenes/sub_scenes/send_egld.yaml
repeat: 1  # optional, defaults to 1
```

For example, let's say you have several transactions to make to assign a given role in your organization to a wallet and you also want to assign this role to several wallets. This can be done elegantly with the scene below:

```yaml
steps:
  - type: Loop
    var_name: USER_FOR_ROLE
    var_list: [françois, jacques, jean]
    steps:
      - type: Scene
        path: assign_role.yaml
```

Then, all of the steps is the scene `assign_role.yaml` should be written while using `%USER_FOR_ROLE` instead of the address of the wallet you want to assign the role to.
This will apply all the steps to françois, jacques and jean without having to copy/paste the steps for each one of them.

(set_vars_step_target)=
### Set Vars Step

This step allows you to directly set some variables within the Scenario data. This will be useful if you need to set some values for generic scenes or if you need to backup some variables
so that they are not overwritten.

```yaml
type: SetVars
variables:
  MyVar: 12312424
  result-backup: "%previously-registered-value"
  nested_values: ["$CONF_VAR", 12421, "%var", {"%account.address": "%saved-value"}]
```

The above example will saves three variables within the scenario data: `MyVar`, `result-backup` and `nested_values`. Their values (or nested values) will be accessible with the `%` symbol (refer to the [smart values chapter](values) for more details of the value system of MxOps).

Note that you can also use [smart-values](values) to create the name of the variable:

```yaml
type: SetVars
variables:
  "%dynamic_name": "%dynamic_value"
  "prefix_%{dynamic_name}_suffix": "%dynamic_value"
```

Lastly, to add clarity, you can also use temporary variables to build what you want step by step:

```yaml
type: SetVars
variables:
  amount_1: "%my_contract.token_1_amount"
  amount_2: "%my_contract.token_2_amount"
  k_factor: "={%{amount_1} * %{amount_2}}"
```


(wait_target)=
### Wait Step

This step allows you to wait for either a certain amount of time or for a certain amount of block production.

To wait for 10.5 seconds:

```yaml
type: Wait
for_seconds: 10.5
```

To wait for 2 block generations on shard 0:

```yaml
type: Wait
for_blocks: 2
shard: 0  # optional, default is metachain
```

```{note}
Waiting for blocks on the chain-simulator network will trigger a call to the chain-simulator to generate the required number of blocks
```

(set_seed_step_target)=
### Set Seed Step

Computer generated numbers are pseudo-random, meaning that we can reproduce the random production if we know the seed (a number) used. This is particularly useful when you want to be able to reproduce a given execution that use random values. This step is here to allow you to set the random seed:

```yaml
type: SetSeed
seed: 42
```

If you don't want to have the exact same random number every time but still want to have a sens of reproducibility, we recommend doing the following:

```yaml
type: SetSeed
seed: "=randint(0,2**32)"  # 2**32-1 is the maximum allowed value for a seed
```

This will generate a random seed and grant you randomness between executions, but if a problem arise, you will be able to inspect the logs to find which seed was used. You may then try to reproduce the error by forcing the seed found in the logs.

```{warning}
Keep in mind that the seed is only set for the current execution of MxOps, meaning that if you execute twice a command with `mxops execute ...` and the seed is set only in the first execution, it will have no impact one the random values generated during the second execution.
```

(assert_step_target)=
### Assert Step

You may want to check that everything is going well by evaluating expressions: did this account receive the correct amount? Is the result of this query as expected? Is the result of this formula correct?
To answer this, you can use the `AssertStep`, that will simply check that all the provided expressions are true.

```yaml
type: Assert
expressions:
  - true
  - 1
  - "={1 > 0}"
  - "={'%{alice.address}' == 'erd1pqslfwszea4hrxdvluhr0v7dhgdfwv6ma70xef79vruwnl7uwkdsyg4xj3'}"
  - "={'item1' in %{my_list}}"
```

This step is really useful combined with [smart-values](values) and with the [step to create variables](set_vars_step_target).


```{note}
Notice that you need to put single quote `'` when you want to execute string comparison.
```

(log_step_target)=
### Log Step

Use this step to log some message, you can use the different logging level available: error, warning, info and debug.
All levels are optional, only use the ones you want.

```yaml
type: Log
error: "Error message %{my_list}"  # optional
warning: "Warning message %{alice.address}"  # optional
info: "Info message ={1+1}"  # optional
debug: "Debug message ={'%{my_list[0]}' + '%{my_list[1]}'}"  # optional
```
