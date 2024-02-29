# Steps

In `MxOps`, any action to be executed is called a `Step`.
In other words, a `Scene` contains a series of `Steps` that tells what `MxOps` should do.

Several type of `Steps` exists, to allow users to easily construct complex `Scenes`.
If you feel something is missing, please make a suggestion in the [github](https://github.com/Catenscia/MxOps/discussions/categories/ideas)!

## Transfer Steps

### EGLD Transfer Step

This step is used to transfer eGLD from an address to another

```yaml
type: EgldTransfer
sender: bob
receiver: alice   # you can also directly write a bech32 address here
amount: 7895651689  # integer amount here (for example 1 EGLD = 1000000000000000000)
```

### Fungible Transfer Step

This step is used to transfer classic (fungible) ESDT from an address to another

```yaml
type: FungibleTransfer
sender: bob
receiver: alice
token_identifier: "MYTOK-a123ec"
amount: 7895651689
```

### Non Fungible Transfer Step

This step is used to transfer a NFT, some SFT or some Meta ESDT from an address to another

```yaml
type: NonFungibleTransfer
sender: bob
receiver: alice
token_identifier: "MTESDT-a123ec"
nonce: 4
amount: 65481 # 1 for NFT
```

### Multi Transfers Step

```yaml
type: MutliTransfers
sender: bob
receiver: alice
transfers:
  - token_identifier: "MYSFT-a123ec"
    amount: 25
    nonce: 4
  - token_identifier: "FUNG-a123ec"
    amount: 87941198416
    nonce: 0 # 0 for fungible ESDT
```

## Contract Steps

### Contract Deploy Step

This `Step` is used to deploy a contract. The address of the new contract will be
saved in the `Scenario` (specified at execution time) under the provided id to allow future interactions.

```yaml
type: ContractDeploy
sender: bob
wasm_path: "path/to/wasm"
abi_path: "path/to/abi"  # optional but stongly recommended
contract_id: my_first_sc
gas_limit: 1584000
arguments: # optional, if any args must be submitted
  - 100
upgradeable: true
readable: false
payable: false
payable_by_sc: true
```

We strongly recommended to provide an ABI with the contract as this will allow `MxOps` to do the data encoding and decoding during queries and calls for you, even if the data is some complex and custom `Struct`.

### Contract Upgrade Step

This `Step` is used to upgrade a contract.

```yaml
type: ContractUpgrade
sender: bob
wasm_path: "path/to/upgraded_wasm"
abi_path: "path/to/abi"  # optional but stongly recommended
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
If you have provided an ABI with the contract, `MxOps` will be able to automatically encode the arguments for your endpoint call, even if they are complex structures. For more details on that, please head to the {doc}`serialization` section.

### Contract Query Step

This `Step` is used to fetch some data from a contract and save it locally for later use in the `Scenario` (specified at execution time).
For example to fetch the identifier of a token created by a contract and stored in a `FungibleTokenMapper` with a view set up as `getEsdtIdentifier`.

```yaml
type: ContractQuery
contract: my_first_sc
endpoint: getEsdtIdentifier
arguments: []
results_save_keys: # optional, key(s) under which save the results of the query
  - EsdtIdentifier
results_types:  # mandatory if results are to be saved and no ABI have been provided for this contract
  - type: TokenIdentifier
print_results: true # optional, if the query results should be printed in the console
```

If you have provided an ABI with the contract, `MxOps` will be able to automatically encode the arguments for your query, even if they are complex structures. For more details on that, please head to the {doc}`serialization` section.
`MxOps` will also automatically decode the response of the query so that if you save the data, you can easily use it again by reference (see {doc}`values`).

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
can_mint: false # optional, defaults to false
can_burn: false # optional, defaults to false
can_change_owner: false # optional, defaults to false
can_upgrade: false # optional, defaults to false
can_add_special_roles: false # optional, defaults to false
```

The results of the transaction will be saved. You can make a reference to this token in later `Steps` using its name, for example to retrieve the token identifier: `%MyToken.identifier`.

```{warning}
To avoid data collision within `MxOps`, `token_name` should be unique within a `Scenario` and should not have a name identical to a `contract_id` in the same `Scenario`.
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
  - ESDTRoleLocalMint
  - ESDTRoleLocalBurn
  - ESDTTransferRole
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
To avoid data collision within `MxOps`, `token_name` should be unique within a `Scenario` and should not have a name identical to a `contract_id` in the same `Scenario`.
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
To avoid data collision within `MxOps`, `token_name` should be unique within a `Scenario` and should not have a name identical to a `contract_id` in the same `Scenario`.
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
To avoid data collision within `MxOps`, `token_name` should be unique within a `Scenario` and should not have a name identical to a `contract_id` in the same `Scenario`.
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
  - ESDTRoleNFTCreate
  - ESDTRoleNFTBurn
  - ESDTRoleNFTUpdateAttributes
  - ESDTRoleNFTAddURI
  - ESDTTransferRole
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
  - ESDTRoleNFTCreate
  - ESDTRoleNFTBurn
  - ESDTRoleNFTAddQuantity
  - ESDTTransferRole
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
  - ESDTRoleNFTCreate
  - ESDTRoleNFTBurn
  - ESDTRoleNFTAddQuantity
  - ESDTTransferRole
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
      - $LOOP_VAR # nonce
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
      - $LOOP_VAR # nonce
      - "%my_first_sc.TokenIdentifier4Amount." # result of the query
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


### Python Step

This step allows to execute a custom python function. You can execute whatever you want in the python function. This `Step` is here to give you maximum flexibility, making `MxOps` suitable for all the needs of you project. Here are some basic use case for the python `Step`:
  - complex calculation (results can be saved as `MxOps` or environment values)
  - complex query parsing
  - randomness generation
  - third party calls (databases, API ...)

For the function, the user can provide raw arguments or can use the MxOps values format.
If the python function return a string, it will be saved as an environment variable under the name `MXOPS_<UPPER_FUNC_NAME>_RESULT`.

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
```

The above `Step` will execute the function `my_function`, located at `./folder/my_module.py` that would look like this:
```python
def my_function(arg_1, arg2, key_1, key_2):
    # execute anything here
    return result  # optionally return a string result
```

You can find examples of python `Steps` in this {doc}`section<../examples/python_steps>`.

```{warning}
MxOps is completely permissive and lets you do anything you want in the python `Step`, including changing the behavior of MxOps itself. Test everything you do on localnet and devnet before taking any action on mainnet.
```

### Scene Step

This step simply runs a `Scene`. It can be used either to organize different executions or more importantly, to avoid copy pasting `Steps`. 

```yaml
type: Scene
scene_path: ./integration_tests/setup_scenes/sub_scenes/send_egld.yaml
```

For example, let's say you have several transactions to make to assign a given role in your organization to a wallet and you also want to assign this role to several wallets. This can be done elegantly with the scene below:

```yaml
steps:
  - type: Loop
    var_name: USER_FOR_ROLE
    var_list: [françois, jacques, jean]
    steps:
      - type: Scene
        scene_path: assign_role.yaml
```

Then, all of the `Steps` is the `Scene` `assign_role.yaml` should be written while using `$USER_FOR_ROLE` instead of the address of the wallet you want to assign the role to.
This will apply all the `Steps` to françois, jacques and jean without having to copy/paste the `Steps` for each one of them.