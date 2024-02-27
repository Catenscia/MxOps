# MxOps

MxOps is a python package created to automate MultiversX transactions: be it smart contracts deployments, calls, queries or just simple transfers. Inspired from DevOps tools and built on top of [mxpy](https://github.com/multiversx/mx-sdk-py-cli), it aims to ease and make reproducible any set of these interactions with the blockchain.

MxOps aims to be useful in these situations:

- deployment automation
- on-chain integration tests
- contract interaction automation


## Quick Overview

Here are some basic uses cases to illustrate how MxOps works.

### Token Mint

```yaml
allowed_networks:
  - devnet
  - localnet

allowed_scenario:
  - "alice_mint"

accounts:  # define the accounts to use
  - account_name: alice
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
      - ESDTRoleLocalMint
      - ESDTRoleLocalBurn
  
  - type: FungibleMint  # make alice mint some tokens
    sender: alice
    token_identifier: "%AliceToken.identifier"
    amount: 100000000  # 100,000.000 ATK

```

### Query with ABI

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
      - 10  # id of the pair to get the details of
    print_results: true
```

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

### Query without ABI

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

```bash
[
    81478482319716395147753,
    4878990096191,
    9390873908175
]
```

### Contract Call with Payments

```yaml
allowed_networks:
  - localnet
  - testnet
  - devnet

allowed_scenario:
  - .*

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

## Getting Started

You have seen above some basic use-cases but MxOps has much more avaible features!
Heads up to the [documentation](https://mxops.readthedocs.io) to get started! You will find tutorials, user documentation and examples 🚀

## Contribution

This tool is an humble proposal by [Catenscia](https://catenscia.com/) to have a standard way of writing deployment files, integration tests and others.
If you want this tool to improve, please tell us your issues and proposals!

And if you're motivated, we will always welcome hepling hands onboard :grin: !

Read the [contribution guidelines](https://github.com/Catenscia/MxOps/blob/main/CONTRIBUTING.md) for more :wink:
