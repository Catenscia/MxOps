# Steps

In MxOps, any action to be executed is called a `Step`.
In other words, a `Scene` contains a series of `Steps` that tell what MxOps should do.

Several type of `Steps` exists, to allow users to easily construct complex `Scenes`.
If you feel something is missing, please make a suggestion in the [github](https://github.com/Catenscia/MxOps/discussions/categories/ideas)!

## Transfer Step

The same step is used to describe any king of transfer: native token, simple esdt, nft, multi-transfers, ...

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

## Contract Steps

### Contract Deploy Step

This `Step` is used to deploy a contract. The address of the new contract will be
saved in the `Scenario` (specified at execution time) under the provided id to allow future interactions.

```yaml
type: ContractDeploy
sender: bob
wasm_path: "path/to/wasm"
abi_path: "path/to/abi"  # optional but strongly recommended
contract_id: my_first_sc
gas_limit: 1584000
arguments: # optional, if any args must be submitted
  - 100
upgradeable: true
readable: false
payable: false
payable_by_sc: true
```

We strongly recommended to provide an ABI with the contract as this will allow MxOps to do the data encoding and decoding during queries and calls for you, even if the data is some complex and custom `Struct`.

### Contract Upgrade Step

This `Step` is used to upgrade a contract.

```yaml
type: ContractUpgrade
sender: bob
wasm_path: "path/to/upgraded_wasm"
abi_path: "path/to/abi"  # optional but strongly recommended
contract: my_first_sc
gas_limit: 1584000
arguments: # optional, if any args must be submitted
  - 100
upgradeable: true
readable: false
payable: false
payable_by_sc: true
```

```{note}
Be mindful of the difference in the argument name between the deploy and the update steps.

`contract_id` can only refer to a contract managed by MxOps whereas `contract` can be any contract. This means that you can upgrade a contract that has not been deployed by MxOps.
```

### Contract Call Step

This `Step` is used to call the endpoint of a deployed contract.

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
  - token_identifier: ALICE-123456
    amount: 58411548
    nonce: 0 # 0 for fungible ESDT
  - token_identifier: LKMEX-e45d41
    amount: 848491898
    nonce: 721
checks: # optional, by default it will contain a transaction success check
  - type: Success
```

To get more information on the `checks` attribute, heads to the {doc}`checks` section.
If you have provided an ABI with the contract, MxOps will be able to automatically encode the arguments for your endpoint call, even if they are complex structures. For more details on that, please head to the {doc}`serialization` section.

(contract_query_target)=
### Contract Query Step

This `Step` is used to fetch some data from a contract and save it locally for later use in the `Scenario` (specified at execution time).
For example to fetch the identifier of a token created by a contract and stored in a `FungibleTokenMapper` with a view set up as `getEsdtIdentifier`.

```yaml
type: ContractQuery
contract: my_first_sc
endpoint: getEsdtIdentifier
arguments: []  # optional, if the view needs any arguments
results_save_keys: # optional, key(s) under which save the results of the query
  - EsdtIdentifier
print_results: true # optional, if the query results should be printed in the console
```

If you have provided an ABI with the contract, MxOps will be able to automatically encode the arguments for your query, even if they are complex structures. For more details on that, please head to the {doc}`serialization` section.
MxOps will also automatically decode the response of the query so that if you save the data, you can easily use it again by reference (see {doc}`values`).

#### About `results_save_keys`

There are several accepted types for `results_save_keys` which will indicated how you want to save the data. You can provided either a master key or some sub-keys or both. The master keys will point to the entire query response whereas sub-keys points to individual result of the queries.
You will find some examples below:



##### Results Save Keys Example 1

Query return type: `(BigUint, BigInt)`

Decoded query response: `[[123456, -7891011]]`

<table style="border: 1px solid black; border-collapse: collapse;">
<tr>
<th style="border: 1px solid black; background-color: #f2f2f2; padding: 8px;">results_save_keys</th>
<th style="border: 1px solid black; background-color: #f2f2f2; padding: 8px;">Data saved within the Scenario</th>
</tr>
<tr>
<td style="border: 1px solid black; background-color: #fff; padding: 8px; font-size: 12px;">
<pre style="margin: 0;">
results_save_keys: master_key
</pre>
</td>
<td style="border: 1px solid black; background-color: #fff; padding: 8px; font-size: 12px;">
<pre style="margin: 0;">
{
  "master_key": [[123456, -7891011]]
}
</pre>
</td>
</tr>
<tr>
<td style="border: 1px solid black; background-color: #fff; padding: 8px; font-size: 12px;">
<pre style="margin: 0;">
results_save_keys:
  master_key:
    - sub_key_1
</pre>
</td>
<td style="border: 1px solid black; background-color: #fff; padding: 8px; font-size: 12px;">
<pre style="margin: 0;">
{
  "master_key": {
    "sub_key_1": [123456, -7891011]
  }
}
</pre>
</td>
</tr>
<tr>
<td style="border: 1px solid black; background-color: #fff; padding: 8px; font-size: 12px;">
<pre style="margin: 0;">
results_save_keys:
  - sub_key_1
</pre>
</td>
<td style="border: 1px solid black; background-color: #fff; padding: 8px; font-size: 12px;">
<pre style="margin: 0;">
{
  "sub_key_1": [123456, -7891011]
}
</pre>
</td>
</tr>
</table>
<p></p>



##### Results Save Keys Example 2

Query return type: `MultiValue2<u32, i8>`

Decoded query response: `[12, -1]`

<table style="border: 1px solid black; border-collapse: collapse;">
<tr>
<th style="border: 1px solid black; background-color: #f2f2f2; padding: 8px;">results_save_keys</th>
<th style="border: 1px solid black; background-color: #f2f2f2; padding: 8px;">Data saved within the Scenario</th>
</tr>
<tr>
<td style="border: 1px solid black; background-color: #fff; padding: 8px; font-size: 12px;">
<pre style="margin: 0;">
results_save_keys: master_key
</pre>
</td>
<td style="border: 1px solid black; background-color: #fff; padding: 8px; font-size: 12px;">
<pre style="margin: 0;">
{
  "master_key": [12, -1]
}
</pre>
</td>
</tr>
<tr>
<td style="border: 1px solid black; background-color: #fff; padding: 8px; font-size: 12px;">
<pre style="margin: 0;">
results_save_keys:
  master_key:
    - sub_key_1
    - sub_key_2
</pre>
</td>
<td style="border: 1px solid black; background-color: #fff; padding: 8px; font-size: 12px;">
<pre style="margin: 0;">
{
  "master_key": {
    "sub_key_1": 12,
    "sub_key_2": -1
  }
}
</pre>
</td>
</tr>
<tr>
<td style="border: 1px solid black; background-color: #fff; padding: 8px; font-size: 12px;">
<pre style="margin: 0;">
results_save_keys:
  - sub_key_1
  - sub_key_2
</pre>
</td>
<td style="border: 1px solid black; background-color: #fff; padding: 8px; font-size: 12px;">
<pre style="margin: 0;">
{
  "sub_key_1": 12,
  "sub_key_2": -1
}
</pre>
</td>
</tr>
</table>
<p></p>



##### Results Save Keys Example 3

Query return type: `MultiValue2<u8, MyStruct<Self::Api>>`

Decoded query response: `[234, {"attribute_1": "WEGLD-abcdef", "attribute_2": 123456}]`

<table style="border: 1px solid black; border-collapse: collapse;">
<tr>
<th style="border: 1px solid black; background-color: #f2f2f2; padding: 8px;">results_save_keys</th>
<th style="border: 1px solid black; background-color: #f2f2f2; padding: 8px;">Data saved within the Scenario</th>
</tr>
<tr>
<td style="border: 1px solid black; background-color: #fff; padding: 8px; font-size: 12px;">
<pre style="margin: 0;">
results_save_keys: master_key
</pre>
</td>
<td style="border: 1px solid black; background-color: #fff; padding: 8px; font-size: 12px;">
<pre style="margin: 0;">
{
  "master_key": [
   234,
   {
      "attribute_1": "WEGLD_abcdef",
      "attribute_2": 123456
   }
  ]
}
</pre>
</td>
</tr>
<tr>
<td style="border: 1px solid black; background-color: #fff; padding: 8px; font-size: 12px;">
<pre style="margin: 0;">
results_save_keys:
  master_key:
    - sub_key_1
    - sub_key_2
</pre>
</td>
<td style="border: 1px solid black; background-color: #fff; padding: 8px; font-size: 12px;">
<pre style="margin: 0;">
{
  "master_key": {
    "sub_key_1": 234,
    "sub_key_2": {
      "attribute_1": "WEGLD_abcdef",
      "attribute_2": 123456
    }
  }
}
</pre>
</td>
</tr>
<tr>
<td style="border: 1px solid black; background-color: #fff; padding: 8px; font-size: 12px;">
<pre style="margin: 0;">
results_save_keys:
  - sub_key_1
  - sub_key_2
</pre>
</td>
<td style="border: 1px solid black; background-color: #fff; padding: 8px; font-size: 12px;">
<pre style="margin: 0;">
{
  "sub_key_1": 234,
  "sub_key_2": {
    "attribute_1": "WEGLD_abcdef",
    "attribute_2": 123456
  }

}
</pre>
</td>
</tr>
</table>
<p></p>

```{warning}
If you provide sub-keys, the number of sub-keys must exactly match the number of elements returned by the query response.
```

(file_fuzzer_target)=
### File Fuzzer Step

This `Step` is used to execute some fuzz testing. The parameters for the tests (queries or calls) are taken from a file.
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
      - token_identifier: TOKEN-abcdef
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

This `Step` is used to issue a new fungible token, a initial supply of tokens will be sent to the issuer.

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

The results of the transaction will be saved. You can make a reference to this token in later `Steps` using its name, for example to retrieve the token identifier: `%MyToken.identifier`.

```{warning}
To avoid data collision within MxOps, `token_name` should be unique within a `Scenario` and should not have a name identical to a `contract_id` in the same `Scenario`.
```

#### Role Management Step

This `Step` is used to set or unset roles for an address on a fungible token.

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

This `Step` is used to mint an additional supply for an already existing fungible token.

```yaml
type: FungibleMint
sender: alice
token_identifier: MTK-abcdef
amount: 100000000
```

### NFT, SFT and Meta Token Steps

Aside from the issuance `Steps`, NFT, SFT and Meta tokens share common methods. The associated steps are listed here.

#### NFT Issuance Step

This `Step` is used to issue a new non fungible token (NFT).

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

The results of the transaction will be saved. You can make a reference to this token in later `Steps` using its name, for example to retrieve the token identifier: `%MyToken.identifier`.

```{warning}
To avoid data collision within MxOps, `token_name` should be unique within a `Scenario` and should not have a name identical to a `contract_id` in the same `Scenario`.
```

#### SFT Issuance Step

This `Step` is used to issue a new semi fungible token (NFT).

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

The results of the transaction will be saved. You can make a reference to this token in later `Steps` using its name, for example to retrieve the token identifier: `%MyToken.identifier`.

```{warning}
To avoid data collision within MxOps, `token_name` should be unique within a `Scenario` and should not have a name identical to a `contract_id` in the same `Scenario`.
```

#### Meta Issuance Step

This `Step` is used to issue a new non fungible token (NFT).

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

The results of the transaction will be saved. You can make a reference to this token in later `Steps` using its name, for example to retrieve the token identifier: `%MyToken.identifier`.

```{warning}
To avoid data collision within MxOps, `token_name` should be unique within a `Scenario` and should not have a name identical to a `contract_id` in the same `Scenario`.
```

#### NFT Role Management Step

This `Step` is used to set or unset roles for an address on a non fungible token.

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

This `Step` is used to set or unset roles for an address on a semi fungible token.

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

This `Step` is used to set or unset roles for an address on a meta token.

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

This `Step` is used to mint a new nonce for an already existing non fungible token.
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

## Miscellaneous Steps

(loop_step_target)=
### Loop Step

This step allows to run a set of steps for a given number of times.
A loop variable is created and can be used as an arguments for the steps inside the loop.

```yaml
# This loop step retrieves the sft tokens that have a nonce between 1 and 100.
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
      - "%LOOP_VAR" # nonce
    results_types:
      - type: BigUint
    results_save_keys:
      - TokenIdentifier4Amount

  - type: ContractCall
    sender: alice
    contract: my_first_sc
    endpoint: RetrieveSft
    gas_limit: 60000000
    arguments:
      - TokenIdentifier4
      - "%LOOP_VAR" # nonce
      - "%my_first_sc.TokenIdentifier4Amount" # result of the query
```

Instead of using `var_start` and `var_end` for the loop variable, a custom list of values can be provided with the keyword `var_list` like below.

```yaml
type: Loop
var_name: LOOP_VAR
var_list: [1, 5, 78, 1566]
steps: [...]
```

You will notice that some symbols are used in the arguments of the above `ContractCall`. These are here to dynamically fetch values from different sources.
Heads up to the {doc}`values` section for more information.

(python_step_target)=
### Python Step

This step allows to execute a custom python function. You can execute whatever you want in the python function. This `Step` is here to give you maximum flexibility, making MxOps suitable for all the needs of you project. Here are some basic use case for the python `Step`:
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
print_result: True  # optional
result_save_key: "my_result"  # optional, key under which save the function result, here it will be accessible as "%my_result"
```

The above `Step` will execute the function `my_function`, located at `./folder/my_module.py` that would look like this:
```python
def my_function(arg_1, arg2, key_1, key_2):
    # execute anything here
    return result
```

You can find examples of python `Steps` in this {doc}`section<../examples/python_steps>`.

```{warning}
MxOps is completely permissive and lets you do anything you want in the python `Step`, including changing the behavior of MxOps itself. Test everything you do on localnet and devnet before taking any action on mainnet.
```

### Scene Step

This step simply runs a `Scene`. It can be used either to organize different executions or more importantly, to avoid copy pasting `Steps`. 

```yaml
type: Scene
path: ./integration_tests/setup_scenes/sub_scenes/send_egld.yaml
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

Then, all of the `Steps` is the `Scene` `assign_role.yaml` should be written while using `%USER_FOR_ROLE` instead of the address of the wallet you want to assign the role to.
This will apply all the `Steps` to françois, jacques and jean without having to copy/paste the `Steps` for each one of them.

(set_vars_step_target)=
### Set Vars Step

This `Step` allows you to directly set some variables within the Scenario data. This will be useful if you need to set some values for generic `Scenes` or if you need to backup some variables
so that they are not overwritten.

```yaml
type: SetVars
variables:
  MyVar: 12312424
  result-backup: "%previously-registered-value"
  nested_values: ["$CONF_VAR", 12421, "%var", {"%account.address": "%saved-value"}]
```

The above example will saves three variables within the `Scenario` data: `MyVar`, `result-backup` and `nested_values`. Their values (or nested values) will be accessible with the `%` symbol (refer to the {doc}`values` section for more details of the value system of MxOps).

(generate_wallets_target)=
### Generate Wallets Step

This `Step` allows you to generate new wallets. For now, only PEM wallets can be generated

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
wallets: ["alice", "bob"]  # generate two wallets names alice and bob
shard: 0  # optional, to force the shard of the generated wallets
```


(r3d4_faucet_target)=
### r3d4 Faucet Step

This `Step` allows you use the devnet and testnet faucet [r3d4](https://r3d4.fr/faucet).
This is a third party tool that is not managed by `Catenscia`, so the compatibility might break.

Some things to keep in mind:
- Respect the limits from r3d4 (1 claim per token per address per day)
- There may be some delays before you receive the funds
- Please don't abuse the faucet, it's a tool useful for a lot of people
- If you have to much funds, send them back to the faucet so that they can be reused
- The faucet only works for devnet and testnet


```yaml
type: R3D4Faucet
targets:
  - alice  # account name handeld by MxOps
  - erd1y3296u7m2v5653pddey3p7l5zacqmsgqc7vsu3w74p9jm2qp3tqqz950yl  # or direct bech32
```

For each address, the maximum amount of EGLD (1 EGLD as of December 2024) will be requested.


(chain_simulator_faucet_target)=
### Chain Simulator Faucet Step

This `Step` allows you to request EGLD on the chain-simulator.

```yaml
type: ChainSimulatorFaucet
amount: 1000000000000000000  # 1.0 EGLD
targets:
  - alice  # account name handeld by MxOps
  - erd1y3296u7m2v5653pddey3p7l5zacqmsgqc7vsu3w74p9jm2qp3tqqz950yl  # or direct bech32
```

(account_clone_target)=
### Account clone step

Exclusive to the chain simulator.
This `Step` allows you to clone an account from another network (ex mainnet) and to import it to the chain simulator.
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
Currently, some clones will even fail because the storage of the account is too big. This will be fixed in the [bernard release](https://github.com/multiversx/mx-chain-go/pull/6547) by the core team.


(wait_target)=
### Wait Step

This `Step` allows you to wait for either a certain amount of time or for a certain amount of block production.

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
