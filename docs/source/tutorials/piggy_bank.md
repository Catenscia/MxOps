# Piggy Bank

This example relies on the MxOps integration test called [Piggy Bank](https://github.com/Catenscia/MxOps/tree/main/integration_tests/piggy_bank).

Step by step, the example will show you how to:

- Automate smart-contract deployments
- Automate smart-contract setups
- Simulate user scenario

## Smart-Contracts

For this example, we have created two smart-contracts: a contract in charge of minting a simple ESDT and a contract that will act as a piggy bank with amazing interest returns.

The image below is a map with the main interactions between these contracts and agents. (click on it for full view).
You will also find some explanation in the next two sections.

```{figure} ../_images/piggy_bank_contracts_map.svg
:alt: Map of interactions between contracts and agents
:align: center
:target: ../_images/piggy_bank_contracts_map.svg
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

### Smart Contract Interactions: User Exploit

We will create the following situation:

- The owner deploys and setup both smart-contracts
- The owner add some airdrop amount to a user
- The user claim the airdrop
- The user deposit and withdraw to/from the piggy-bank several times to exploit the contracts

We will call this situation "User Exploit" and create a special folder for the corresponding scenes.

#### EsdtMinter Initialization

Let's create out first scene to deploy the `esdt-minter` contract: `mxops_scenes/user_exploit/01_esdt_minter_init.yaml`.

##### Deployment

Our first step will be to deploy the `esdt-minter` contract.
The only argument we need to supply is the interest percentage. Let's set it to 100%.
We will give the deployed contract the id "abc-esdt-minter". (ABC will be the name of the token that will be issued).

```yaml
type: ContractDeploy
sender: owner
wasm_path: "./contracts/esdt-minter/output/esdt-minter.wasm"
abi_path: "./contracts/esdt-minter/output/esdt-minter.abi.json"
contract_id: "abc-esdt-minter"
gas_limit: 50000000
arguments:
    - 100
upgradeable: true
readable: false
payable: false
payable_by_sc: true
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

We want to retrieve the token identifier that has been assigned to the newly issued token. For that we can execute a query to access the view on the ESDTmapper from the contract.
We will save this identifier as a string under the name `EsdtIdentifier`.

```yaml
type: ContractQuery
contract: "abc-esdt-minter"
endpoint: getEsdtIdentifier
arguments: []
results_save_keys:
  - EsdtIdentifier
```

#### PiggyBank Initialization

We create a new scene to deploy and initialize the `piggy-bank` contract: `mxops_scenes/user_exploit/02_piggy_bank_init.yaml`.

##### Deployment

When we deploy the `piggy-bank` contract, we need to supply two arguments: the token identifier of the token that will be accepted by the contract and the address of the token issuer.

We could supply theses values by hand but that would be a huge waste of time and very prone to errors. Instead we can use the [smart-values](../user_documentation/values) system of MxOps:

We can access the address of the `esdt-minter` contract we just deployed by using its id: `%abc-esdt-minter.address`.
As we also save the token identifier, we can access it too: `%abc-esdt-minter.EsdtIdentifier`.

```yaml
type: ContractDeploy
sender: owner
wasm_path: "./contracts/piggy-bank/output/piggy-bank.wasm"
wasm_path: "./contracts/piggy-bank/output/piggy-bank.abi.json"
contract_id: "abc-piggy-bank"
gas_limit: 80000000
arguments:
    - "%abc-esdt-minter.EsdtIdentifier"
    - "%abc-esdt-minter.address"
upgradeable: true
readable: false
payable: false
payable_by_sc: true
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
    - "%abc-piggy-bank.address"
```

#### Airdrop

In the scene `mxops_scenes/user_exploit/03_airdrop.yaml`, the owner will add an airdrop of 100.000 ABC for the user and the user will claim this airdrop:

```yaml
steps:
  - type: ContractCall
    sender: owner
    contract: "abc-esdt-minter"
    endpoint: addAirdropAmount
    gas_limit: 5000000
    arguments:
      - "%user.address"
      - 100000

  - type: ContractCall
    sender: user
    contract: "abc-esdt-minter"
    endpoint: claimAirdrop
    gas_limit: 5000000
    checks:
      - type: Success

      - type: Transfers
        condition: exact
        expected_transfers:
          - sender: "%abc-esdt-minter.address"
            receiver: "%user.address"
            identifier: "%abc-esdt-minter.EsdtIdentifier"
            amount: 100000
```

#### Money Print

The final scene will be `mxops_scenes/user_exploit/04_money_print.yaml`
Once he claimed the airdrop, the user discover that he can earn tons of ABC tokens by depositing and withdrawing his tokens to/from the `piggy-bank`. To test his hypothesis, he will execute three cycles of deposit and withdraws. As the interest is 100%, the user should double his tokens amount each cycle.

We will execute this scenario using a `LoopStep`. The loop variable will be the amount that the user deposit at each cycle: 100.000 then 200.000 and finally 400.000 (We assume he deposits each time all the tokens he has).

```yaml
allowed_networks:
  - localnet
  - testnet
  - devnet

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
          - identifier: "%abc-esdt-minter.EsdtIdentifier"
            amount: "%CAPITAL_AMOUNT"
            nonce: 0
        gas_limit: 8000000

      - type: ContractCall
        sender: user
        contract: "abc-piggy-bank"
        endpoint: withdraw
        gas_limit: 8000000
```

### Execution

We can now execute our scenes in a scenario. We will execute this on devnet for example and call our scenario "piggy_bank_user_exploit".

#### Data Cleaning

As we are making some tests, we may want to delete the data from any previous execution.

```bash
mxops \
    data \
    delete \
    -n devnet \
    -s piggy_bank_user_exploit
```

Enter `y` when prompted.

#### Scenes Execution

The first scene we need to execute is the scene with devnet accounts to allow the other scenes to use them.
After that we can execute all the scenes in the order we wrote them.

```bash
mxops \
    execute \
    -n devnet \
    -s piggy_bank_user_exploit \
    mxops_scenes/accounts/devnet_accounts.yaml \
    mxops_scenes
```

This should give you on output similar to this:

```bash
[2025-04-03 16:55:13,692 INFO] MxOps  Copyright (C) 2025  Catenscia
This program comes with ABSOLUTELY NO WARRANTY [general in main_cli.py:65]
[2025-04-03 16:55:13,693 INFO] Deletion of the scenario integration_test_piggy_bank_user_exploit on devnet [data in execution_data.py:901]
[2025-04-03 16:55:13,693 WARNING] Scenario integration_test_piggy_bank_user_exploit on devnet do not exist [data in execution_data.py:915]
[2025-04-03 16:55:13,693 INFO] Scenario integration_test_piggy_bank_user_exploit created for network devnet [data in execution_data.py:864]
[2025-04-03 16:55:13,693 INFO] Executing scene integration_tests/setup_scenes/01_accounts.yaml [execution in scene.py:148]
[2025-04-03 16:55:14,469 INFO] Executing scene integration_tests/piggy_bank/mxops_scenes/user_exploit/01_esdt_minter_init.yaml [execution in scene.py:148]
[2025-04-03 16:55:14,474 INFO] Deploying contract abc-esdt-minter [execution in smart_contract.py:66]
[2025-04-03 16:55:20,804 INFO] Transaction successful: https://devnet-explorer.multiversx.com/transaction/40737bb6dd6debd1909c46826dc8c556aa7373b72c23c68226d0130de6b30114 [execution in base.py:163]
[2025-04-03 16:55:20,814 INFO] The address of the deployed contract abc-esdt-minter is erd1qqqqqqqqqqqqqpgqk447s8kd9hs0wyu4u3y30ezd9pcky799dwnsxa89kc [execution in smart_contract.py:121]
[2025-04-03 16:55:20,818 INFO] Calling issueToken on erd1qqqqqqqqqqqqqpgqk447s8kd9hs0wyu4u3y30ezd9pcky799dwnsxa89kc (abc-esdt-minter)  [execution in smart_contract.py:243]
[2025-04-03 16:55:52,319 INFO] Transaction successful: https://devnet-explorer.multiversx.com/transaction/412620047543fe7fc3b873fc0d316ccc33fe41bc830f0e444e9c1e03b9615f8e [execution in base.py:163]
[2025-04-03 16:55:52,321 INFO] Query getEsdtIdentifier on erd1qqqqqqqqqqqqqpgqk447s8kd9hs0wyu4u3y30ezd9pcky799dwnsxa89kc (abc-esdt-minter) [execution in smart_contract.py:362]
[2025-04-03 16:55:52,379 INFO] Query results: {
    "EsdtIdentifier": "ABC-07ea83"
} [execution in smart_contract.py:390]
[2025-04-03 16:55:52,380 INFO] Executing scene integration_tests/piggy_bank/mxops_scenes/user_exploit/02_piggy_bank_init.yaml [execution in scene.py:148]
[2025-04-03 16:55:52,385 INFO] Deploying contract abc-piggy-bank [execution in smart_contract.py:66]
[2025-04-03 16:55:58,683 INFO] Transaction successful: https://devnet-explorer.multiversx.com/transaction/5dbd007a2800b4333902d6df09e761edf8b9c348a4063711b3c147e991644d8c [execution in base.py:163]
[2025-04-03 16:55:58,684 INFO] The address of the deployed contract abc-piggy-bank is erd1qqqqqqqqqqqqqpgqjm274hr0aeaashrq0jnwr7qdpr670pt9dwnsk65s39 [execution in smart_contract.py:121]
[2025-04-03 16:55:58,696 INFO] Calling addInterestAddress on erd1qqqqqqqqqqqqqpgqk447s8kd9hs0wyu4u3y30ezd9pcky799dwnsxa89kc (abc-esdt-minter)  [execution in smart_contract.py:243]
[2025-04-03 16:56:04,936 INFO] Transaction successful: https://devnet-explorer.multiversx.com/transaction/908b44558e0d555e8f0ac319daf9a914e8566223fe74c24a8547b9d8bd745570 [execution in base.py:163]
[2025-04-03 16:56:04,938 INFO] Executing scene integration_tests/piggy_bank/mxops_scenes/user_exploit/03_airdrop.yaml [execution in scene.py:148]
[2025-04-03 16:56:04,942 INFO] Calling addAirdropAmount on erd1qqqqqqqqqqqqqpgqk447s8kd9hs0wyu4u3y30ezd9pcky799dwnsxa89kc (abc-esdt-minter)  [execution in smart_contract.py:243]
[2025-04-03 16:56:11,164 INFO] Transaction successful: https://devnet-explorer.multiversx.com/transaction/fd9ba9d4657d79902228a9262628b86bbad10fcd4c7b6b48ece696a4f54828f8 [execution in base.py:163]
[2025-04-03 16:56:11,167 INFO] Calling claimAirdrop on erd1qqqqqqqqqqqqqpgqk447s8kd9hs0wyu4u3y30ezd9pcky799dwnsxa89kc (abc-esdt-minter)  [execution in smart_contract.py:243]
[2025-04-03 16:56:17,416 INFO] Transaction successful: https://devnet-explorer.multiversx.com/transaction/7171ff26451308810edbfdeefb5c235fbe6adbec21795112da7d763c7578ace9 [execution in base.py:163]
[2025-04-03 16:56:17,418 INFO] Call results: {
    "thomas_airdrop_amount": 100000
} [execution in smart_contract.py:315]
[2025-04-03 16:56:17,427 INFO] Executing python function check_storage from user module checks [execution in msc.py:197]
[2025-04-03 16:56:17,428 INFO] Function result: null [execution in msc.py:220]
[2025-04-03 16:56:17,429 INFO] Executing scene integration_tests/piggy_bank/mxops_scenes/user_exploit/04_money_print.yaml [execution in scene.py:148]
[2025-04-03 16:56:17,434 INFO] Calling deposit on erd1qqqqqqqqqqqqqpgqjm274hr0aeaashrq0jnwr7qdpr670pt9dwnsk65s39 (abc-piggy-bank)  [execution in smart_contract.py:243]
[2025-04-03 16:56:20,587 INFO] Transaction successful: https://devnet-explorer.multiversx.com/transaction/0c46717a3329acee2e4ad72c75cff8ad879046f7b4343976ec4bea00369126eb [execution in base.py:163]
[2025-04-03 16:56:20,588 INFO] Calling withdraw on erd1qqqqqqqqqqqqqpgqjm274hr0aeaashrq0jnwr7qdpr670pt9dwnsk65s39 (abc-piggy-bank)  [execution in smart_contract.py:243]
[2025-04-03 16:56:26,828 INFO] Transaction successful: https://devnet-explorer.multiversx.com/transaction/a12b4c097c865f7f96ae764319a9c2b4a8647d695d5412eb698d44851f96bcd7 [execution in base.py:163]
[2025-04-03 16:56:26,832 INFO] Calling deposit on erd1qqqqqqqqqqqqqpgqjm274hr0aeaashrq0jnwr7qdpr670pt9dwnsk65s39 (abc-piggy-bank)  [execution in smart_contract.py:243]
[2025-04-03 16:56:33,056 INFO] Transaction successful: https://devnet-explorer.multiversx.com/transaction/fafe50707be245b177439bada1dd130b177dfa00f9388c566ee6cf3c9fca9c59 [execution in base.py:163]
[2025-04-03 16:56:33,059 INFO] Calling withdraw on erd1qqqqqqqqqqqqqpgqjm274hr0aeaashrq0jnwr7qdpr670pt9dwnsk65s39 (abc-piggy-bank)  [execution in smart_contract.py:243]
[2025-04-03 16:56:39,276 INFO] Transaction successful: https://devnet-explorer.multiversx.com/transaction/f8925079fcf4b6af4cc1f062b2bce01efcd770912ca3469e3e932a7bff65aea4 [execution in base.py:163]
[2025-04-03 16:56:39,280 INFO] Calling deposit on erd1qqqqqqqqqqqqqpgqjm274hr0aeaashrq0jnwr7qdpr670pt9dwnsk65s39 (abc-piggy-bank)  [execution in smart_contract.py:243]
[2025-04-03 16:56:45,518 INFO] Transaction successful: https://devnet-explorer.multiversx.com/transaction/7f49b941900921915634cb9ab928b33e35a545eee94808378526b2e9f7695911 [execution in base.py:163]
[2025-04-03 16:56:45,521 INFO] Calling withdraw on erd1qqqqqqqqqqqqqpgqjm274hr0aeaashrq0jnwr7qdpr670pt9dwnsk65s39 (abc-piggy-bank)  [execution in smart_contract.py:243]
[2025-04-03 16:56:51,761 INFO] Transaction successful: https://devnet-explorer.multiversx.com/transaction/a5a81ded7dcd3591c03b19530a4ad8d4e388d12727c86b08b4fc1602dc808341 [execution in base.py:163]
```

And that's it! We have a repeatable way of executing deployment and interactions with smart-contracts! 🥳

Using the links in the previous outputs, you can navigate the different transactions with the explorer.