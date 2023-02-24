# Piggy Bank

This example uses the smart-contracts and `Scenes` from the `MxOps` integration test called [Piggy Bank](https://github.com/Catenscia/MxOps/tree/main/integration_tests/piggy_bank).

Step by step, the example will show you how to:

- Automate smart-contract deployments
- Automate smart-contract setups
- Simulate user scenario

## Smart-Contracts

For this example, we have created two smart-contracts: a contract in charge of minting a simple ESDT and a contract that will act as a piggy bank with amazing interest returns.

The image below is a map with the main interactions between these contracts and agents. (click on it for full view).
You will also find some explanation in the next two sections.

```{thumbnail} ../images/piggy_bank_contracts_map.svg
```

```{warning}
DISCLAIMER: This should be obvious but these contracts are not meant to be use on real use cases as their designs are flawed for the example purposes.
```

### EsdtMinter Contract

This contract has three roles:

- Issue a new token
- Allow airdrops to specific users
- Mint new tokens to pay the interests of the piggy-bank

Find more details in the [source code](https://github.com/Catenscia/MxOps/tree/main/integration_tests/piggy_bank/contracts/esdt-minter/src).

### PiggyBank Contract

A user can deposit a specific token in the bank. The only other action he can make is to withdraw them. At withdrawal, he will get back his principal and receive some interests in addition.

Find more details in the [source code](https://github.com/Catenscia/MxOps/tree/main/integration_tests/piggy_bank/contracts/piggy-bank/src).

## Scenes

Now that we have some smart-contracts, we can construct some `Scenes`.
We will create a scenes folder at the root level of our smart-contract project. Here is what our structure looks like:

```bash
.
├── contracts/
│   ├── esdt-minter
│   ├── piggy-bank
│   ├── tests
│   └── Cargo.toml
├── mxops_scenes
├── scripts
├── wallets/
│   ├── alice.pem
│   ├── bob.pem
│   ├── devnet_owner.pem
│   └── devnet_user.pem
└── Cargo.toml
```

### Accounts

We would like to execute our contracts on two chains: On the devnet to ensure everything will work flawlessly but also on a localnet to make our first tests without spamming the devnet.

We will copy two wallets, alice and bob, that already have some eGLD on their account when we start a localnet.

For the devnet we will create two wallets, one for the owner of the contracts and one for a user. We will provide some eGLD to these accounts using the [devnet wallet](https://devnet-wallet.multiversx.com/).

To access these wallets from several scenes, we will create specific `Scene` for them.

#### Localnet Accounts

We will use bob as the contract owner and alice as a user.

```yaml
allowed_networks:
  - LOCAL

allowed_scenario:
  - "piggy_bank.*"

accounts:
  - account_name: owner
    pem_path: ./wallets/bob.pem
  - account_name: user
    pem_path: ./wallets/alice.pem
```

#### Devnet Accounts

Same as above, but we replace the wallets by the ones on the devnet and we change the allowed network.

```yaml
allowed_networks:
  - DEV

allowed_scenario:
  - "piggy_bank.*"

accounts:
  - account_name: owner
    pem_path: ./wallets/bob.pem
  - account_name: user
    pem_path: ./wallets/alice.pem
```

#### Result Structure

Our project should now be like this:

```bash
.
├── contract/
│   ├── esdt-minter
│   ├── piggy-bank
│   ├── tests
│   └── Cargo.toml
├── mxops_scenes/
│   └── accounts/
│       ├── local_accounts.yaml
│       └── devent_account.yaml
├── scripts
├── wallets/
│   ├── alice.pem
│   ├── bob.pem
│   ├── devnet_owner.pem
│   └── devnet_user.pem
└── Cargo.toml
```

### Smart Contract Interactions: User Exploit

We will create the following situation:

- The owner deploys and setup both smart-contracts
- The owner add some airdrop amount to a user
- The user claim the airdrop
- The user deposit and withdraw to/from the piggy-bank several times to exploit the contracts

We will call this situation "User Exploit" and create a special folder for the corresponding scenes.

```bash
.
├── contract/
│   ├── esdt-minter
│   ├── piggy-bank
│   ├── tests
│   └── Cargo.toml
├── mxops_scenes/
│   └── accounts/
│       ├── local_accounts.yaml
│       └── devent_account.yaml
├────── user_exploit/
├── scripts
├── wallets/
│   ├── alice.pem
│   ├── bob.pem
│   ├── devnet_owner.pem
│   └── devnet_user.pem
└── Cargo.toml
```

#### EsdtMinter Initialization

Let's create out first scene to deploy the `esdt-minter` contract: `mxops_scenes/user_exploit/01_esdt_minter_init.yaml`.

We will allow this scene (and all the next scenes) to be run on all networks except the mainnet. We will then specify that the scenarios we will use should start with 'piggy_bank' to restrict execution mistakes:

```yaml
allowed_networks:
  - LOCAL
  - TEST
  - DEV

allowed_scenario:
  - "piggy_bank.*"
```

##### Deployment

Our first step will be to deploy the `esdt-minter` contract.
The only argument we need to supply is the interest percentage. Let's set it to 100%.
We will give the deployed contract the id "abc-esdt-minter". (ABC will be the name of the token that will be issued).

```yaml
type: ContractDeploy
sender: owner
wasm_path: "./contracts/esdt-minter/output/esdt-minter.wasm"
contract_id: "abc-esdt-minter"
gas_limit: 50000000
arguments:
    - 100
upgradeable: True
readable: False
payable: False
payable_by_sc: True
```

##### Token Issuance

We will now ask the contract to issue a new fungible ESDT named "ABC". This token should have 3 decimals.
To issue a new token, we also need to pay some eGLD. The amount change depending on the network but this value is present in the [MxOps' default configuration](https://github.com/Catenscia/MxOps/blob/main/mxops/resources/default_config.ini) under the name `BASE_ISSUING_COST`.

```yaml
type: ContractCall
sender: owner
contract: "abc-esdt-minter"
endpoint: issueToken
gas_limit: 100000000
value: "&BASE_ISSUING_COST"
arguments:
    - ABC
    - ABC
    - 3
```

##### Token Identifier

We want to retrieve the token identifier that has been assigned to the newly issued token. For that we can use a query to access the view on the ESDTmapper from the contract.
We will save this identifier as a string under the name `EsdtIdentifier`.

```yaml
type: ContractQuery
contract: "abc-esdt-minter"
endpoint: getEsdtIdentifier
arguments: []
expected_results:
    - save_key: EsdtIdentifier
    result_type: str
print_results: True
```

##### Results

Our file `mxops_scenes/user_exploit/01_esdt_minter_init.yaml` should now look like this:

```yaml
allowed_networks:
  - LOCAL
  - TEST
  - DEV

allowed_scenario:
  - "piggy_bank.*"

steps:
  - type: ContractDeploy
    sender: owner
    wasm_path: "./contracts/esdt-minter/output/esdt-minter.wasm"
    contract_id: "abc-esdt-minter"
    gas_limit: 50000000
    arguments:
      - 100
    upgradeable: True
    readable: False
    payable: False
    payable_by_sc: True

  - type: ContractCall
    sender: owner
    contract: "abc-esdt-minter"
    endpoint: issueToken
    gas_limit: 100000000
    value: "&BASE_ISSUING_COST"
    arguments:
      - ABC
      - ABC
      - 3
  
  - type: ContractQuery
    contract: "abc-esdt-minter"
    endpoint: getEsdtIdentifier
    arguments: []
    expected_results:
      - save_key: EsdtIdentifier
        result_type: str
    print_results: True
```

#### PiggyBank Initialization

We create a new scene to deploy and initialize the `piggy-bank` contract: `mxops_scenes/user_exploit/02_piggy_bank_init.yaml`.

##### Deployment

When we deploy the `piggy-bank` contract, we need to supply two arguments: the token identifier of the token that will be accepted by the contract and the address of the token issuer.

We could supply theses values by hand but that would be a huge waste of time and very prone to errors. Instead we can use the {doc}`../user_documentation/values` system of `MxOps`:

We can access the address of the `esdt-minter` contract we just deployed by using its id: `%abc-esdt-minter%address`.
As we also save the token identifier, we can access it too: `%abc-esdt-minter%EsdtIdentifier`.

```yaml
type: ContractDeploy
sender: owner
wasm_path: "./contracts/piggy-bank/output/piggy-bank.wasm"
contract_id: "abc-piggy-bank"
gas_limit: 80000000
arguments:
    - "%abc-esdt-minter%EsdtIdentifier"
    - "%abc-esdt-minter%address"
upgradeable: True
readable: False
payable: False
payable_by_sc: True
```

##### Interest Whitelist

The `esdt-contract` only allows whitelisted addresses to claim interests. We need to add our `piggy-bank` contract to this whitelist using the endpoint `addInterestAddress`.

```yaml
type: ContractCall
sender: owner
contract: "abc-esdt-minter"
endpoint: addInterestAddress
gas_limit: 5000000
arguments:
    - "%abc-piggy-bank%address"
```

##### Results

The file `mxops_scenes/user_exploit/02_piggy_bank_init.yaml` should look like this:

```yaml
allowed_networks:
  - LOCAL
  - TEST
  - DEV

allowed_scenario:
  - "piggy_bank.*"

steps:
  - type: ContractDeploy
    sender: owner
    wasm_path: "./contracts/piggy-bank/output/piggy-bank.wasm"
    contract_id: "abc-piggy-bank"
    gas_limit: 80000000
    arguments:
      - "%abc-esdt-minter%EsdtIdentifier"
      - "%abc-esdt-minter%address"
    upgradeable: True
    readable: False
    payable: False
    payable_by_sc: True

  - type: ContractCall
    sender: owner
    contract: "abc-esdt-minter"
    endpoint: addInterestAddress
    gas_limit: 5000000
    arguments:
      - "%abc-piggy-bank%address"
```

#### Airdrop

In the scene `mxops_scenes/user_exploit/03_airdrop.yaml`, the owner will add an airdrop of 100.000 ABC for the user and the user will claim this airdrop:

```yaml
allowed_networks:
  - LOCAL
  - TEST
  - DEV

allowed_scenario:
  - "piggy_bank.*"

steps:
  - type: ContractCall
    sender: owner
    contract: "abc-esdt-minter"
    endpoint: addAirdropAmount
    gas_limit: 5000000
    arguments:
      - "[user]"
      - 100000

  - type: ContractCall
    sender: user
    contract: "abc-esdt-minter"
    endpoint: claimAirdrop
    gas_limit: 5000000
```

#### Money Print

The final scene will be `mxops_scenes/user_exploit/04_money_print.yaml`
Once he claimed the airdrop, the user discover that he can earn tons of ABC tokens by depositing and withdrawing his tokens to/from the `piggy-bank`. To test his hypothesis, he will execute three cycles of deposit and withdraws. As the interest is 100%, the user should double his tokens amount each cycle.

We will execute this scenario using a `LoopStep`. The loop variable will be the amount that the user deposit at each cycle: 100.000 then 200.000 and finally 400.000 (We assume he deposits each time all the tokens he has).

```yaml
allowed_networks:
  - LOCAL
  - TEST
  - DEV

allowed_scenario:
  - "piggy_bank.*"

steps:
  - type: Loop
    var_name: CAPITAL_AMOUNT
    var_list: [100000, 200000, 400000]
    steps:
      - type: ContractCall
        sender: user
        contract: "abc-piggy-bank"
        endpoint: deposit
        esdt_transfers:
          - token_identifier: "%abc-esdt-minter%EsdtIdentifier"
            amount: "$CAPITAL_AMOUNT:int"
            nonce: 0
        gas_limit: 8000000

      - type: ContractCall
        sender: user
        contract: "abc-piggy-bank"
        endpoint: withdraw
        gas_limit: 8000000
```

#### Result Structure

Our project should now be like this:

```bash
.
├── contract/
│   ├── esdt-minter
│   ├── piggy-bank
│   ├── tests
│   └── Cargo.toml
├── mxops_scenes/
│   ├── accounts/
│   │   ├── local_accounts.yaml
│   │   └── devent_account.yaml
├────── user_exploit/
│       ├── 01_esdt_minter_init.yaml
│       ├── 02_piggy_bank_init.yaml
│       ├── 03_airdrop.yaml
│       └── 04_money_print.yaml
├── scripts
├── wallets/
│   ├── alice.pem
│   ├── bob.pem
│   ├── devnet_owner.pem
│   └── devnet_user.pem
└── Cargo.toml
```

### Execution

We can now execute our scenes in a `Scenario`. We will execute this on the devnet for example and call our scenario "piggy_bank_user_exploit".

#### Data Cleaning

As we are making some tests, we want to delete the data from any previous execution.

```bash
mxops \
    data \
    delete \
    -n DEV \
    -s piggy_bank_user_exploit
```

Enter `y` when prompted.

#### Scenes Execution

The first `Scene` we need to execute is the `Scene` with the devnet accounts to allow the other `Scenes` to use them.
After that we can execute all the `Scenes`in the order we wrote them.

```bash
mxops \
    execute \
    -n DEV \
    -s piggy_bank_user_exploit \
    mxops_scenes/accounts/devnet_accounts.yaml \
    mxops_scenes
```

This should give you on output similar to this:

```bash
MxOps  Copyright (C) 2023  Catenscia
This program comes with ABSOLUTELY NO WARRANTY
[2023-01-24 21:26:45,650 data INFO] Scenario piggy_bank_user_exploit created for network DEV [data:259 in create_scenario]
[2023-01-24 21:26:45,650 scene INFO] Executing scene mxops_scenes/accounts/devnet_accounts.yaml [scene:68 in execute_scene]
[2023-01-24 21:26:46,099 scene INFO] Executing scene mxops_scenes/user_exploit/01_esdt_minter_init.yaml [scene:68 in execute_scene]
[2023-01-24 21:26:46,121 steps INFO] Deploying contract abc-esdt-minter [steps:106 in execute]
[2023-01-24 21:26:51,645 steps INFO] Deploy successful on erd1qqqqqqqqqqqqqpgqam5fmdvqqta307y4xe6elhqj4z58leduhzdq8jytfw
tx hash: https://devnet-explorer.multiversx.com/transactions/2bf47375abc692ecc284fd1a273ca4ad7dbec677da548466aa85eedf7bd5140e [steps:126 in execute]
[2023-01-24 21:26:51,647 steps INFO] Calling issueToken for abc-esdt-minter [steps:175 in execute]
[2023-01-24 21:27:23,416 steps INFO] Call successful: https://devnet-explorer.multiversx.com/transactions/0f80e6e44eb1c742d1837c8871edffe1f6f329230634674588e406c09636e0fd [steps:192 in execute]
[2023-01-24 21:27:23,416 steps INFO] Query on getEsdtIdentifier for abc-esdt-minter [steps:214 in execute]
[{'base64': 'QUJDLTE0YWYwZA==', 'hex': '4142432d313461663064', 'number': 308176147074667304595556}]
[2023-01-24 21:27:23,631 steps INFO] Saving Query results as contract data [steps:228 in execute]
[2023-01-24 21:27:23,631 steps INFO] Query successful [steps:236 in execute]
[2023-01-24 21:27:23,636 scene INFO] Executing scene mxops_scenes/user_exploit/02_piggy_bank_init.yaml [scene:68 in execute_scene]
[2023-01-24 21:27:23,653 steps INFO] Deploying contract abc-piggy-bank [steps:106 in execute]
[2023-01-24 21:27:34,681 steps INFO] Deploy successful on erd1qqqqqqqqqqqqqpgqn7jctdfnem2n2zk8atus7ep9r64jy80whzdqp3wmyu
tx hash: https://devnet-explorer.multiversx.com/transactions/9f2f45f2ea9d33dc4700bef2724ec4a42e8a21737a60c02004cef05609d04493 [steps:126 in execute]
[2023-01-24 21:27:34,682 steps INFO] Calling addInterestAddress for abc-esdt-minter [steps:175 in execute]
[2023-01-24 21:27:40,258 steps INFO] Call successful: https://devnet-explorer.multiversx.com/transactions/c3022dab7a49a5eefe2a4c17ccc66838eb41e3280a6c14f0c81d9169773a9810 [steps:192 in execute]
[2023-01-24 21:27:40,259 scene INFO] Executing scene mxops_scenes/user_exploit/03_airdrop.yaml [scene:68 in execute_scene]
[2023-01-24 21:27:40,261 steps INFO] Calling addAirdropAmount for abc-esdt-minter [steps:175 in execute]
[2023-01-24 21:27:45,579 steps INFO] Call successful: https://devnet-explorer.multiversx.com/transactions/88beda7d9b4858f32010137fd4e7c5ca573cfae18dccbe0a163001de4474b5a5 [steps:192 in execute]
[2023-01-24 21:27:45,580 steps INFO] Calling claimAirdrop for abc-esdt-minter [steps:175 in execute]
[2023-01-24 21:28:37,922 steps INFO] Call successful: https://devnet-explorer.multiversx.com/transactions/d8451a30fedcd92d67b8e783cb3989e1613143d09cd3cd9303a011bcb29caa2d [steps:192 in execute]
[2023-01-24 21:28:37,923 scene INFO] Executing scene mxops_scenes/user_exploit/04_money_print.yaml [scene:68 in execute_scene]
[2023-01-24 21:28:37,926 steps INFO] Calling deposit for abc-piggy-bank [steps:175 in execute]
[2023-01-24 21:29:30,292 steps INFO] Call successful: https://devnet-explorer.multiversx.com/transactions/95fc37a627fcfbea102fb4f317880b39b7b76effd4399bdb15075e6926481c1e [steps:192 in execute]
[2023-01-24 21:29:30,292 steps INFO] Calling withdraw for abc-piggy-bank [steps:175 in execute]
[2023-01-24 21:30:28,589 steps INFO] Call successful: https://devnet-explorer.multiversx.com/transactions/33d52b9ed973757d09782998bd096ff19ba3ad0e42fb4810fc7430941d7b50be [steps:192 in execute]
[2023-01-24 21:30:28,590 steps INFO] Calling deposit for abc-piggy-bank [steps:175 in execute]
[2023-01-24 21:31:21,530 steps INFO] Call successful: https://devnet-explorer.multiversx.com/transactions/2d3da6f3251b3d8194d5bf2ad7e42215bf496c0440b364f901d661a7899e160e [steps:192 in execute]
[2023-01-24 21:31:21,530 steps INFO] Calling withdraw for abc-piggy-bank [steps:175 in execute]
[2023-01-24 21:32:13,874 steps INFO] Call successful: https://devnet-explorer.multiversx.com/transactions/97a5b1699b287561f5bf8f5cbadf90fb42f8abf08a398f0f55b74bca5b643891 [steps:192 in execute]
[2023-01-24 21:32:13,874 steps INFO] Calling deposit for abc-piggy-bank [steps:175 in execute]
[2023-01-24 21:33:06,208 steps INFO] Call successful: https://devnet-explorer.multiversx.com/transactions/da79b69f16c20768a85d48c29225af5c99699b4ffe57c459a46160a66aca36c5 [steps:192 in execute]
[2023-01-24 21:33:06,208 steps INFO] Calling withdraw for abc-piggy-bank [steps:175 in execute]
[2023-01-24 21:34:03,874 steps INFO] Call successful: https://devnet-explorer.multiversx.com/transactions/086d02d7341727aaa89ac09e45bd438aae16ea36b8d46a0723913b4e64968183 [steps:192 in execute]
```

And that's it! You just created a repeatable way of executing interactions with your smart-contracts! 🥳

Using the links in the previous outputs, you can navigate the different transactions with the explorer.

## Data

After executing, the `Scenario` data is persistent (until you delete or overwrite it).
You can access this data using command lines.

For example, to see all the data saved under our piggy_bank_user_exploit `Scenario`:

```bash
mxops data get -n DEV -s piggy_bank_user_exploit
```

This should give you a result similar to this:

```bash
MxOps  Copyright (C) 2023  Catenscia
This program comes with ABSOLUTELY NO WARRANTY
[2023-01-24 21:36:14,175 data INFO] Scenario piggy_bank_user_exploit loaded for network DEV [data:234 in load_scenario]
{
    "name": "piggy_bank_user_exploit",
    "network": "DEV",
    "creation_time": 1674592005,
    "last_update_time": 1674592054,
    "contracts_data": {
        "abc-esdt-minter": {
            "contract_id": "abc-esdt-minter",
            "address": "erd1qqqqqqqqqqqqqpgqam5fmdvqqta307y4xe6elhqj4z58leduhzdq8jytfw",
            "wasm_hash": "c8280fa4f2f173940f3ba9e0b294867e3fad910ae0744628a90a0b73452c12cd",
            "deploy_time": 1674592008,
            "last_upgrade_time": 1674592008,
            "saved_values": {
                "EsdtIdentifier": "ABC-14af0d"
            }
        },
        "abc-piggy-bank": {
            "contract_id": "abc-piggy-bank",
            "address": "erd1qqqqqqqqqqqqqpgqn7jctdfnem2n2zk8atus7ep9r64jy80whzdqp3wmyu",
            "wasm_hash": "ea2a4cf5e924d01b3e43541edce4180e5972e46d50c10fa4db62b3b11c0d8699",
            "deploy_time": 1674592050,
            "last_upgrade_time": 1674592050,
            "saved_values": {}
        }
    }
}
```
