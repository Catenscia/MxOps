# MxOps

![MxOps full logo](./docs/source/_images/mxops_full_logo.png)


MxOps is a python package created to automate MultiversX transactions: be it smart contracts deployments, calls, queries or just simple transfers. Inspired from DevOps tools and built on top of [mx-sdk-py](https://github.com/multiversx/mx-sdk-py), it aims to ease and make reproducible any interaction with the blockchain.

MxOps targets a broad audience of users and developers, by providing a clear, easy to read and write syntax, even for non technical users.

MxOps aims to be particularely useful in these situations:

- deployment automation
- on-chain integration tests
- contract interaction automation

## Sponsors

MxOps is an open-source tool dedicated to enhancing the MultiversX ecosystem, and its development and maintenance rely on the generous support of our sponsors.

We extend our heartfelt thanks to **[Astrarizon](https://www.astrarizon.com)**, the first sponsor of MxOps! ([announcement on X](https://x.com/Astrarizon/status/1861791446099263552))

![MxOps full logo](./docs/source/_images/astrarizon_logo.png)

If MxOps has been beneficial in your projects or professional endeavors, we invite you to join our community of sponsors. Your support will ensure the continued maintenance and future development of MxOps, helping to keep this tool at the forefront of the MultiversX ecosystem. Interested? Reach out to us at [contact@catenscia.com](mailto:contact@catenscia.com).


## Quick Overview

Here are some basic uses cases to illustrate how MxOps works.

### Token Mint

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

### Query with ABI

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
    print_results: true
```

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

## Getting Started

You have seen above some basic use-cases but MxOps has much more avaible features!
Heads up to the [documentation](https://mxops.readthedocs.io) to get started! You will find tutorials, user documentation and examples 🚀

## Contribution

This tool is an humble proposal by [Catenscia](https://catenscia.com/) to have a standard way of writing deployment files, integration tests and others.
If you want this tool to improve, please tell us your issues and proposals!

And if you're motivated, we will always welcome hepling hands onboard :grin: !

Read the [contribution guidelines](https://github.com/Catenscia/MxOps/blob/main/CONTRIBUTING.md) for more :wink:
