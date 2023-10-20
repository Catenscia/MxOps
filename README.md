# MxOps

MxOps is a python package created to automate MultiversX transactions: be it smart contracts deployments, calls, queries or just simple transfers. Inspired from DevOps tools and built on top of [mxpy](https://github.com/multiversx/mx-sdk-py-cli), it aims to ease and make reproducible any set of these interactions with the blockchain.

MxOps aims to be useful in these situations:

- deployment automation
- on-chain integration tests
- contract interaction automation

For a quick overview, here's how to create a token, assign a mint role and mint tokens with MxOps:

```yaml
allowed_networks:
  - devnet
  - localnet

allowed_scenario:
  - "alice_mint"

accounts:
  - account_name: alice
    pem_path: ./wallets/alice.pem

steps:
  - type: FungibleIssue
    sender: alice
    token_name: AliceToken
    token_ticker: ATK
    initial_supply: 1000000000  # 1,000,000.000 ATK
    num_decimals: 3
    can_add_special_roles: true

  - type: ManageFungibleTokenRoles
    sender: alice
    is_set: true    # if we want to set or unset the roles below
    token_identifier: "%AliceToken.identifier"
    target: alice
    roles:
      - ESDTRoleLocalMint
      - ESDTRoleLocalBurn
  
  - type: FungibleMint
    sender: alice
    token_identifier: "%AliceToken.identifier"
    amount: 100000000  # 100,000.000 ATK

```

## Getting Started

Heads up to the [documentation](https://mxops.readthedocs.io) to get started! You will find tutorials, user documentation and examples 🚀

## Contribution

This tool is an humble proposal by [Catenscia](https://catenscia.com/) to have a standard way of writing deployment files, integration tests and others.
If you want this tool to improve, please tell us your issues and proposals!

And if you're motivated, we will always welcome hepling hands onboard :grin: !

Read the [contribution guidelines](https://github.com/Catenscia/MxOps/blob/main/CONTRIBUTING.md) for more :wink:
