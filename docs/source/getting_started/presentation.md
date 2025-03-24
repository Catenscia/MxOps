# MxOps Presentation

```{figure} ../_images/mxops_full_logo.png
:alt: MxOps Logo
:align: center
:target: ../_images/mxops_full_logo.png
```

MxOps is a python package created to facilitate and automate MultiversX interactions: be it smart contracts deployments, calls, queries or just simple transfers. Inspired from DevOps tools and built on top of [mx-sdk-py](https://github.com/multiversx/mx-sdk-py), it aims to ease and make reproducible any set of these interactions with the blockchain.

MxOps aims to be useful in these situations:

- deployment automation
- on-chain integration tests
- contract interaction automation

## Quick Overview

Here are some basic uses cases to illustrate how MxOps works and give a very brief overview of what it looks like.

### Token Mint

Here, MxOps is used to issue a fungible token, assign mint and burn roles to the issuer and then mint some token.

```yaml
accounts:  # define the accounts to use
  - account_id: alice
    pem_path: ./wallets/alice.pem

steps:
  - type: FungibleIssue  # Issue the fungible token
    sender: alice
    token_name: AliceToken
    token_ticker: ATK
    initial_supply: 1000000000  # 1,000,000.000 ATK
    num_decimals: 3
    can_add_special_roles: true

  - type: ManageFungibleTokenRoles  # assign mint and burn roles to alice
    sender: alice
    is_set: true
    token_identifier: "%AliceToken.identifier"
    target: alice
    roles:
      - local_mint
      - local_burn
  
  - type: FungibleMint  # make alice mint some tokens
    sender: alice
    token_identifier: "%AliceToken.identifier"
    amount: 100000000  # 100,000.000 ATK
```

### Contract Query

MxOps is used below to fetch information from the [live Onedex contract](https://explorer.multiversx.com/accounts/erd1qqqqqqqqqqqqqpgqqz6vp9y50ep867vnr296mqf3dduh6guvmvlsu3sujc) on the mainnet. We specifically query the state of the pool n°10. This example relies on the ABI definition of the Onedex smart-contract.

```yaml
allowed_networks:
    - mainnet

accounts:
  - account_id: onedex-swap
    address: erd1qqqqqqqqqqqqqpgqqz6vp9y50ep867vnr296mqf3dduh6guvmvlsu3sujc
    abi_path: ./abis/onedex-sc.abi.json

steps:

  - type: ContractQuery
    contract: onedex-swap
    endpoint: viewPair
    arguments:
      - 10  # id of the pair to get the details of
```

Printed results:
```bash
[
    {
        "pair_id": 10,
        "state": {
            "__discriminant__": 1,
            "__name__": "Active"
        },
        "enabled": true,
        "owner": "erd1rfs4pg224d2wmndmntvu2dhfhesmuda6m502vt5mfctn3wg7tu4sk6rtku",
        "first_token_id": "MPH-f8ea2b",
        "second_token_id": "USDC-c76f1f",
        "lp_token_id": "MPHUSDC-777138",
        "lp_token_decimal": 18,
        "first_token_reserve": 15,
        "second_token_reserve": 2331925,
        "lp_token_supply": 393944771203191982,
        "lp_token_roles_are_set": true
    }
]
```

### Contract Call with Payments

Here, MxOps is used to call a contract while sending tokens. The example shows what it would look like to add some liquidity to a pool.

```yaml
steps:
  - type: ContractCall
    sender: thomas
    contract: pair-contract
    endpoint: addLiquidity
    arguments:
      - 984849849765987  # (min amount out for slippage protection)
    esdt_transfers:
      - token_identifier: TOKENA-abcdef
        amount: 894916519846515
        nonce: 0
      - token_identifier: TOKENB-abcdef
        amount: 710549841216484
        nonce: 0
    gas_limit: 12000000
```

These examples illustrate very simple interactions but MxOps offers you much more: dynamic values, data save, data environment, direct reusability across different networks (mainnet, devnet, localnet...), interactions with any external tools such as databases, APIs ...
It is a tool that is fully permissive and allows you to create highly customized experiences for your projects. With these teasers in mind, we let you continue your discovery of MxOps 😉

## User Flow

MxOps works with simple yaml files called `Scenes` that look like the examples shown above. In these `Scenes` you will simply describe the different elements that will be used to interact with the blockchain.
During execution, MxOps will save some data locally on your computer, for example:

- deployment addresses for newly deployed contracts
- token identifier for newly issued tokens
- query results when asked by the user

This data is accessible to MxOps and can be reused within any of your `Scenes`.

Here is a little illustration of what is happening (click on it to zoom-in):

```{figure} ../_images/mxops_illustration.svg
:alt: User flow on MxOps
:align: center
:target: ../_images/mxops_illustration.svg
```


If you are a bit confused by this illustration, don't worry: the only thing you will have to do as a user is to write `Scenes` and execute them. Next paragraph gives you a broad understanding of the constitution of a `Scene`.

## Scenes

A `Scene` is a file describing what MxOps has to do. If we translate it in natural language, it would look like the following:

  ```bash
  - MxOps can execute this scene on the mainnet and devnet
  - Name "owner" the wallet located at "./wallets/my_devnet_wallet.pem"
  - MxOps will execute these actions in the specified order:
      - Make "owner" deploy a contract from wasm file at "./contracts/my_contract.wasm".
        Name the newly deployed contract "my-contract".
      - Make "owner" call the endpoint "stake" of the contract "my-contract"
        while sending 0.5 eGLD.
      - Query the view "getStakedAmount" of the contract "my-contract"
        while providing the address of "owner" as argument and store the
        result under the key "ownerStakedAmount"
      - Make "owner" call the endpoint "withdraw" of the contract "my-contract"
        while providing these arguments: ["ownerStakedAmount"]
  ```

Here is the above `Scene`, but this time with the MxOps syntax:

  ```yaml
  allowed_networks:
    - devnet
    - mainnet

  allowed_scenario:
    - deploy_stake_withdraw

  accounts:
    - account_id: owner
      pem_path: ./wallets/my_devnet_wallet.pem

  steps:
    - type: ContractDeploy
      sender: owner
      wasm_path: ./contracts/my_contract.wasm
      abi_path: ./contracts/my_contract.abi.json
      contract_id: my-contract
      gas_limit: 50000000
      upgradeable: true
      readable: false
      payable: false
      payable_by_sc: true

    - type: ContractCall
      sender: owner
      contract: my-contract
      endpoint: stake
      gas_limit: 100000000
      value: 50000000000000000
    
    - type: ContractQuery
      contract: my-contract
      endpoint: getStakedAmount
      arguments:
          - "%owner.address"
      results_save_keys:
        - ownerStakedAmount

    - type: ContractCall
      sender: owner
      contract: my-contract
      endpoint: withdraw
      gas_limit: 5000000
      arguments:
        - "%my-contract.ownerStakedAmount"

  ```

A lot of information is written here, but you don't have to worry about the details for now. Just remember that `Scenes` are the core of MxOps and that it tells the program what to do.

You will be guided through the steps of writing a `Scene` in the next sections. But before that, you need to 🚧 {doc}`install MxOps! <installation>` 🚧
