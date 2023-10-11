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
receiver: alice # you can also write bech32 address here
amount: 7895651689
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
contract_id: my_first_sc
gas_limit: 1584000
arguments: # optional, if any args must be submitted
  - 100
upgradeable: true
readable: false
payable: false
payable_by_sc: true
```

### Contract Upgrade Step

This `Step` is used to upgrade a contract.

```yaml
type: ContractUpgrade
sender: bob
wasm_path: "path/to/upgraded_wasm"
contract: my_first_sc
gas_limit: 1584000
arguments: # optional, if any args must be submitted
  - 100
upgradeable: true
readable: false
payable: false
payable_by_sc: true
```

```{warning}
Be mindful of the difference in the argument name between the deploy and the update steps.

`contract_id` can only refer to contract managed by MxOps whereas `contract` can be any contract.
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
value: 0 # optional, amount of eGLD to send
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

### Contract Query Step

This `Step` is used to fetch some data from a contract and save it locally for later use in the `Scenario` (specified at execution time).
For example to fetch the identifier of a token created by a contract and stored in a `FungibleTokenMapper` with a view set up as `getEsdtIdentifier`.

```yaml
type: ContractQuery
contract: my_first_sc
endpoint: getEsdtIdentifier
arguments: []
expected_results: # list of results excpected from the query output
  - save_key: EsdtIdentifier
    result_type: str
print_results: false # if the query results should be printed in the console
```

Currently allowed values for `result_type`: [`int`, `str`]

(loop_step_target)=

## Token Management Steps

### Fungible Token Steps

#### Issuance Step

This `Step` is used to issue a new fungible token, a initial supply of tokens will be sent to the issuer.

```yaml
type: FungibleIssue
sender: alice
token_name: MyToken # must be unique in a Scenario
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
is_set: true # if false, this will unset the provided roles
token_identifier: MTK-abcdef
target: erd17jcn20jh2k868vg0mm7yh0trdd5mxpy4jzasaf2uraffpae0yrjsvu6txw
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
token_name: MyNFT # must be unique in a Scenario
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
token_name: MySFT # must be unique in a Scenario
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
token_name: MyMeta # must be unique in a Scenario
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
is_set: true # if false, this will unset the provided roles
token_identifier: MNFT-abcdef
target: erd17jcn20jh2k868vg0mm7yh0trdd5mxpy4jzasaf2uraffpae0yrjsvu6txw
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
is_set: true # if false, this will unset the provided roles
token_identifier: MNFT-abcdef
target: erd17jcn20jh2k868vg0mm7yh0trdd5mxpy4jzasaf2uraffpae0yrjsvu6txw
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
is_set: true # if false, this will unset the provided roles
token_identifier: META-abcdef
target: erd17jcn20jh2k868vg0mm7yh0trdd5mxpy4jzasaf2uraffpae0yrjsvu6txw
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

### Loop Step

This steps allows to run a set of steps for a given number of times.
A loop variable is created and can be used as an arguments for the steps inside the loop.

```yaml
# This loop step retrieve the sft tokens with a nonce between 1 and 100.
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
    expected_results:
      - save_key: TokenIdentifier4Amount
        result_type: int

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

This steps allows to execute a custom python function. You can execute whatever you want in the python function. This `Step` is here to give you maximum flexibility, making `MxOps` suitable for all the needs of you project. Here are some basic use case for the python `Step`:
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