# Tutorial

This tutorial uses the smart-contracts and `Scenes` from `MxOps` [integration tests](https://github.com/Catenscia/MxOps/tree/main/integration_tests).

This will guide you through every steps required to run a complete example with MxOps. After this tutorial, you will have learn to:

- Automate deploiments
- Automate smart-contract setups
- Simulate user scenario

In future version of `MxOps`, you will also be able to test queries and calls results.

## Smart-Contracts

To use `MxOps`, we first need some smart-contracts. We will create two of them: a simple contract that is in charge of minting a fungible ESDT and a contract that will act as a piggy bank that gives amazing interest returns.

The image below is a map with the main interactions betweens these contracts and agents. (click on it for full view).
You will also find some explanation in the next two sections.

```{thumbnail} ../images/integration_test_contracts_map.svg
```

```{warning}
DISCLAIMER: This should be obvious but these contracts are not meant to be use on real usecases as their designs are flawed for the tutorial purposes.
```

### EsdtMinter Contract

This contract has three roles:

- Issue a new token
- Allow airdrops to specific users
- Mint new tokens to pay the interests of the piggy-bank

Don't hesitate to check the [source code](https://github.com/Catenscia/MxOps/tree/main/integration_tests/contracts/esdt-minter/src) for more details.

### PiggyBank Contract

A user can deposit a specific token in the bank. The only other action he can make is to withdraw them. At withdrawal, he will get back his principal and receive some interests in addition.

Don't hesitate to check the [source code](https://github.com/Catenscia/MxOps/tree/main/integration_tests/contracts/piggy-bank/src) for more details.

## Scenes

Now that we home some smart-contracts, we can contructs some `Scenes`.
We will create a scenes folder at the root level of our smart-contract projet. Here is what our structure looks like:

```bash
.
├── contracts/
│   ├── esdt-minter
│   ├── piggy-bank
│   ├── tests
│   └── Cargo.toml
├── scenes
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

We will copy two wallets, alice and bob, that already have some egld on their account when we start a localnet.

For the devnet we will create two wallets, one for the owner of the contracts and one for a user. We will provide some egld to these accounts using the [devnet wallet](https://devnet-wallet.multiversx.com/).

To access these wallets from several scenes, we will create specific `Scenes̀for them.

#### LocalNet Accounts

We will use bob as the contract owner and alice as a user.

```yaml
allowed_networks:
  - LOCAL

allowed_scenario:
  - "integration_tests*"

accounts:
  - account_name: owner
    pem_path: ./integration_tests/wallets/bob.pem
  - account_name: user
    pem_path: ./integration_tests/wallets/alice.pem
```

#### Devnet Accounts

Same as above, but we replace the wallets by the ones on the devnet and we change the allowed network.

```yaml
allowed_networks:
  - LOCAL

allowed_scenario:
  - "integration_tests*"

accounts:
  - account_name: owner
    pem_path: ./integration_tests/wallets/bob.pem
  - account_name: user
    pem_path: ./integration_tests/wallets/alice.pem
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
├── scenes/
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

### Smart Contract Interactions

We will create the following situation:

- The owner deploys and setup both smart-contracts
- The owner add some airdrop amount to a user
- The user claim the airdrop
- The user deposit and withdraw to/from the piggy-bank several times to exploit the contracts

#### EsdtMinter Initialisation

Let's create out first scene to deploy the `esdt-minter` contract: `scenes/01_esdt_minter_init.yaml`.

We will allow this scene (and all the next scenes) to be run on all networks except the mainnet. The scenario we will use should also start with 'integration_test':

```yaml
allowed_networks:
  - LOCAL
  - TEST
  - DEV

allowed_scenario:
  - "integration_test*"
```

##### Deployment

Our first step will be to deploy the `esdt-minter` contract.
The only argument we need to supply is the interest percentage. Let's set it to 100%.
We will give the deployed contract the id "abc-esdt-minter". (ABC will be the name of the token that will be issued).

```yaml
type: ContractDeploy
sender: owner
wasm_path: "./integration_tests/contracts/esdt-minter/output/esdt-minter.wasm"
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
To issue a new token, we also need to pay some egld. The amount change depending on the network but this value is present in the [MxOps' config](https://github.com/Catenscia/MxOps/blob/main/mxops/resources/default_config.ini) under the name `BASE_ISSUING_COST`.

```yaml
type: ContractCall
sender: owner
contract_id: "abc-esdt-minter"
endpoint: issueToken
gas_limit: 100000000
value: "&BASE_ISSUING_COST"
arguments:
    - ABC
    - ABC
    - 3
```

##### Token Identifier

We want to retrieve the token identifier that has been assigned to the newly issued token. For that we can use a query to access the view on the esdt mapper from the contract.
We will save this identifier as a string under the name "EsdtIdentifier".

```yaml
type: ContractQuery
contract_id: "abc-esdt-minter"
endpoint: getEsdtIdentifier
arguments: []
expected_results:
    - save_key: EsdtIdentifier
    result_type: str
print_results: True
```

##### Results

Our file `scenes/01_esdt_minter_init.yaml` should now look like this:

```yaml
allowed_networks:
  - LOCAL
  - TEST
  - DEV

allowed_scenario:
  - "integration_test*"

steps:
  - type: ContractDeploy
    sender: owner
    wasm_path: "./integration_tests/contracts/esdt-minter/output/esdt-minter.wasm"
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
    contract_id: "abc-esdt-minter"
    endpoint: issueToken
    gas_limit: 100000000
    value: "&BASE_ISSUING_COST"
    arguments:
      - ABC
      - ABC
      - 3
  
  - type: ContractQuery
    contract_id: "abc-esdt-minter"
    endpoint: getEsdtIdentifier
    arguments: []
    expected_results:
      - save_key: EsdtIdentifier
        result_type: str
    print_results: True
```

#### PiggyBank Intitialisation

We create a new scene to deploy and initialize the `piggy-bank` contract: `scenes/02_piggy_bank_init.yaml`.

##### Deployment

When we deploy the `piggy-bank` contract, we need to supply two arguments: the token identifier of the token that will be accepted by the contract and the address of the token issuer.

We could supply theses values by hand but that would be a huge waste of time and very prone to errors. Instead we can use the {doc}`values` system of `MxOps`:

We can access the address of the `esdt-minter` contract we just deployed by using its id: "%abc-esdt-minter%address".
As we also save the token identifier, we can access it too: "%abc-esdt-minter%EsdtIdentifier".

```yaml
type: ContractDeploy
sender: owner
wasm_path: "./integration_tests/contracts/piggy-bank/output/piggy-bank.wasm"
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

The `esdt-contract` only allows whitelisted addresses to claim interests. We need to add our `piggy-bank` contract to this withelist using the endpoint `addInterestAddress`.

```yaml
type: ContractCall
sender: owner
contract_id: "abc-esdt-minter"
endpoint: addInterestAddress
gas_limit: 5000000
arguments:
    - "%abc-piggy-bank%address"
```

##### Results

The file `scenes/02_piggy_bank_init.yaml` should look like this:

```yaml
allowed_networks:
  - LOCAL
  - TEST
  - DEV

allowed_scenario:
  - "integration_test*"

steps:
  - type: ContractDeploy
    sender: owner
    wasm_path: "./integration_tests/contracts/piggy-bank/output/piggy-bank.wasm"
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
    contract_id: "abc-esdt-minter"
    endpoint: addInterestAddress
    gas_limit: 5000000
    arguments:
      - "%abc-piggy-bank%address"
```

#### Airdrop

In the scene `scenes/03_airdrop.yaml`, the owner will add an airdrop of 100.000 ABC for the user and the user will claim this airdrop:

```yaml
allowed_networks:
  - LOCAL
  - TEST
  - DEV

allowed_scenario:
  - "integration_test*"

steps:
  - type: ContractCall
    sender: owner
    contract_id: "abc-esdt-minter"
    endpoint: addAirdropAmount
    gas_limit: 5000000
    arguments:
      - "[user]"
      - 100000

  - type: ContractCall
    sender: user
    contract_id: "abc-esdt-minter"
    endpoint: claimAirdrop
    gas_limit: 5000000
```

#### Money Printing

Once he claimed the airdrop, the user discover that he can earn tons of ABC tokens by depositing and withdrawing his tokens to/from the `piggy-bank`. To test his hypothesis, he will execute three cycles of deposit and withdraws. As the interest is 100%, the user should double his tokens amount each cycle.

We will execute this scenario using a `LoopStep`. The loop variable will be the amount that the user deposit at each cycle: 100.000 then 200.000 and finally 400.000 (We assume he deposits each time all the tokens he has).

```yaml
allowed_networks:
  - LOCAL
  - TEST
  - DEV

allowed_scenario:
  - "integration_test*"

steps:
  - type: Loop
    var_name: CAPITAL_AMOUNT
    var_list: [100000, 200000, 400000]
    steps:
      - type: ContractCall
        sender: user
        contract_id: "abc-piggy-bank"
        endpoint: deposit
        esdt_transfers:
          - token_identifier: "%abc-esdt-minter%EsdtIdentifier"
            amount: "$CAPITAL_AMOUNT:int"
            nonce: 0
        gas_limit: 8000000

      - type: ContractCall
        sender: user
        contract_id: "abc-piggy-bank"
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
├── scenes/
│   ├── accounts/
│   │   ├── local_accounts.yaml
│   │   └── devent_account.yaml
│   ├── 01_esdt_minter_init.yaml
│   ├── 02_piggy_bank_init.yaml
│   ├── 03_airdrop.yaml
│   └── 04_money_print.yaml
├── scripts
├── wallets/
│   ├── alice.pem
│   ├── bob.pem
│   ├── devnet_owner.pem
│   └── devnet_user.pem
└── Cargo.toml
```

### Execution

We can now execute our scenes in a `Scenario`. We will execute this on the devnet for example and call our scenario "integration_tests_tutorial".

#### Data Cleaning

As we are making some tests, we want to delete the data from any previous execution.

```bash
mxops \
    data \
    delete \
    -n DEV \
    -s integration_tests_tutorial
```

Enter `y` when prompted.

#### Scenes Execution

The first `Scene` we need to execute is the `Scene` with the devnet accounts to allow the other `Scenes` to use them.
After that we can execute all the `Scenes`in the order we wrote them.

```bash
mxops \
    execute \
    -n DEV \
    -s integration_tests_tutorial \
    scenes/accounts/devnet_accounts.yaml \
    scenes
```

This sould give you on output similar to this:

```bash
MxOps  Copyright (C) 2023  Catenscia
This program comes with ABSOLUTELY NO WARRANTY
[2023-01-24 08:12:26,030 data INFO] Scenario integration_tests created for network DEV [data:259 in create_scenario]
[2023-01-24 08:12:26,030 scene INFO] Executing scene integration_tests/scenes/accounts/devnet_accounts.yaml [scene:68 in execute_scene]
[2023-01-24 08:12:26,411 scene INFO] Executing scene integration_tests/scenes/01_esdt_minter_init.yaml [scene:68 in execute_scene]
[2023-01-24 08:12:26,415 steps INFO] Deploying contract abc-esdt-minter [steps:106 in execute]
[2023-01-24 08:12:32,185 steps INFO] Deploy successful on erd1qqqqqqqqqqqqqpgqv6p829acqhv0z42jdvlp688xr7hcaax6hzdqcyjy04
tx hash: https://devnet-explorer.multiversx.com/transactions/9f18f2b28920d50cc2f78de2597e8119949cccb07b23f0b0122d87c6887ccbc4 [steps:126 in execute]
[2023-01-24 08:12:32,187 steps INFO] Calling issueToken for abc-esdt-minter [steps:175 in execute]
[2023-01-24 08:13:04,101 steps INFO] Call successful: https://devnet-explorer.multiversx.com/transactions/03bbdee5935e9fd7cb89343d1e43c7c81a2d146dbcd0f79b136abca02c4b9eae [steps:192 in execute]
[2023-01-24 08:13:04,102 steps INFO] Query on getEsdtIdentifier for abc-esdt-minter [steps:214 in execute]
[{'base64': 'QUJDLWYwOTNjNg==', 'hex': '4142432d663039336336', 'number': 308176147132923566580534}]
[2023-01-24 08:13:04,815 steps INFO] Saving Query results as contract data [steps:228 in execute]
[2023-01-24 08:13:04,815 steps INFO] Query successful [steps:236 in execute]
[2023-01-24 08:13:04,820 scene INFO] Executing scene integration_tests/scenes/02_piggy_bank_init.yaml [scene:68 in execute_scene]
[2023-01-24 08:13:04,823 steps INFO] Deploying contract abc-piggy-bank [steps:106 in execute]
[2023-01-24 08:13:10,679 steps INFO] Deploy successful on erd1qqqqqqqqqqqqqpgqq9g7qtphjvp254x29zzvxhu6fje2c300hzdqlhqrpj
tx hash: https://devnet-explorer.multiversx.com/transactions/e5f3ee67fe17a335619dd2f523c0cc409caebdaab6ffbfa2c1c02d0a9a1cea7c [steps:126 in execute]
[2023-01-24 08:13:10,680 steps INFO] Calling addInterestAddress for abc-esdt-minter [steps:175 in execute]
[2023-01-24 08:13:16,097 steps INFO] Call successful: https://devnet-explorer.multiversx.com/transactions/6b7d29c6d53058aa2b553f60ae5272971816ab2f3e5525c0a054735194dedfab [steps:192 in execute]
[2023-01-24 08:13:16,098 scene INFO] Executing scene integration_tests/scenes/03_airdrop.yaml [scene:68 in execute_scene]
[2023-01-24 08:13:16,101 steps INFO] Calling addAirdropAmount for abc-esdt-minter [steps:175 in execute]
[2023-01-24 08:13:21,636 steps INFO] Call successful: https://devnet-explorer.multiversx.com/transactions/aa7e587c72e60ae4796b5e0b82196d93cba50d0fa081fe971dbee6e70ce58312 [steps:192 in execute]
[2023-01-24 08:13:21,636 steps INFO] Calling claimAirdrop for abc-esdt-minter [steps:175 in execute]
[2023-01-24 08:14:13,946 steps INFO] Call successful: https://devnet-explorer.multiversx.com/transactions/1a8f4d8a84e24b05c1b17173a5c10a2c4a5e60aa26df7c14ad3e00690aa79189 [steps:192 in execute]
[2023-01-24 08:14:13,947 scene INFO] Executing scene integration_tests/scenes/04_money_print.yaml [scene:68 in execute_scene]
[2023-01-24 08:14:13,951 steps INFO] Calling deposit for abc-piggy-bank [steps:175 in execute]
[2023-01-24 08:15:11,150 steps INFO] Call successful: https://devnet-explorer.multiversx.com/transactions/a40421d170696f36171693e63e87ad2f825603a37fdd39e421641965c8f85414 [steps:192 in execute]
[2023-01-24 08:15:11,150 steps INFO] Calling withdraw for abc-piggy-bank [steps:175 in execute]
[2023-01-24 08:16:03,628 steps INFO] Call successful: https://devnet-explorer.multiversx.com/transactions/4136c5e6932229329ffd406ccda4830f799aa48e2f871520ea4346a145c75037 [steps:192 in execute]
[2023-01-24 08:16:03,628 steps INFO] Calling deposit for abc-piggy-bank [steps:175 in execute]
[2023-01-24 08:16:56,012 steps INFO] Call successful: https://devnet-explorer.multiversx.com/transactions/c33479dc324d06a0a00570789b2eefbd3b4605fcf186169886532d50235e3d33 [steps:192 in execute]
[2023-01-24 08:16:56,012 steps INFO] Calling withdraw for abc-piggy-bank [steps:175 in execute]
[2023-01-24 08:17:55,076 steps INFO] Call successful: https://devnet-explorer.multiversx.com/transactions/2adbb9201b2d26d9aab3c0c840ac0cb8ca2c75ccb2441bbce0e52f34c45ca4f0 [steps:192 in execute]
[2023-01-24 08:17:55,076 steps INFO] Calling deposit for abc-piggy-bank [steps:175 in execute]
[2023-01-24 08:18:52,833 steps INFO] Call successful: https://devnet-explorer.multiversx.com/transactions/2d709f1e3ffc64c0f69ccc6a9c325c556f970f864d6dfae720a8a86d8e6dcceb [steps:192 in execute]
[2023-01-24 08:18:52,834 steps INFO] Calling withdraw for abc-piggy-bank [steps:175 in execute]
[2023-01-24 08:19:45,517 steps INFO] Call successful: https://devnet-explorer.multiversx.com/transactions/6e9ddbadbbe849a93e740ca7ff1cf95e4aaac4014f8bb3c653834932409a2e56 [steps:192 in execute]
```

And that's it! You just created a repetable way of executing interactions with your smart-contracts! 🥳

Using the links in the previous outputs, you can navigate the different transactions with the explorer.

## Data

After executing, the `Scenario` data is persitent (until you delete or overwrite it).
You can access this data using command lines.

For example, to see all the data saved under our integration_tests_tutorial `Scenario`:

```bash
mxops data get -n DEV -s integration_tests_tutorial
```

This should give you a result similar to this:

```bash
MxOps  Copyright (C) 2023  Catenscia
This program comes with ABSOLUTELY NO WARRANTY
[2023-01-24 09:24:33,620 data INFO] Scenario integration_tests loaded for network DEV [data:234 in load_scenario]
{
    "name": "integration_tests",
    "network": "DEV",
    "creation_time": 1674547946,
    "last_update_time": 1674547990,
    "contracts_data": {
        "abc-esdt-minter": {
            "contract_id": "abc-esdt-minter",
            "address": "erd1qqqqqqqqqqqqqpgqv6p829acqhv0z42jdvlp688xr7hcaax6hzdqcyjy04",
            "wasm_hash": "c8280fa4f2f173940f3ba9e0b294867e3fad910ae0744628a90a0b73452c12cd",
            "deploy_time": 1674547950,
            "last_upgrade_time": 1674547950,
            "saved_values": {
                "EsdtIdentifier": "ABC-f093c6"
            }
        },
        "abc-piggy-bank": {
            "contract_id": "abc-piggy-bank",
            "address": "erd1qqqqqqqqqqqqqpgqq9g7qtphjvp254x29zzvxhu6fje2c300hzdqlhqrpj",
            "wasm_hash": "ea2a4cf5e924d01b3e43541edce4180e5972e46d50c10fa4db62b3b11c0d8699",
            "deploy_time": 1674547986,
            "last_upgrade_time": 1674547986,
            "saved_values": {}
        }
    }
}
```

## Conclusion

You are now ready to write your own `Scenes` 👏👏👏

Please don't hesitate to give us your feedback on [github](https://github.com/Catenscia/MxOps/discussions) or [twitter](https://twitter.com/catenscia), we would really appreciate it 🤗
