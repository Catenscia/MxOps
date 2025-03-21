# ChangeLog

## Unreleased

### Fixed

- Inconsistent data path due the snap packages
- Remove deprecated help description files and use direct descriptors
- ReadTheDocs build with uv

### Added

- the data save path of `MxOps` is now configurable through the config var `DATA_PATH`
- chain-simulator network and adapted transaction schema (forward chain until transaction completion)
- `FileFuzzerStep`
- Account's addresses are now saved within the `Scenario` data at load time. They can be referenced to with "%account_id.address"
- `SetVarsStep`
- `GenerateWalletsStep`
- `R3D4FaucetStep`
- `ChainSimulatorFaucetStep`
- `LoopStep` can now directly use a list from the Scenario data
- `ChainSimulatorFaucetStep` and `R3D4FaucetStep` can now directly use a list from the Scenario data as targets
- `WaitStep`
- classes for smart values to rationalize the conversion of smart values
- Formulas can be directly supplied as arguments within MxOps scenes
- chain-simulator can be started and stopped from MxOps
- results for smart-contract calls can now be saved too
- skip simulator transaction signature when the sender account is unknown
- `AccountCloneStep`
- a file cache system per network
- account cloning now use the cache system
- id can now be given to any account
- user accounts are now auto reloaded from scenario data (no need to supply them at each execution)
- SceneStep can now be repeated
- SceneStep can now target a folder of scenes


### Changed

- 🚨 BREAKING CHANGE 🚨 loop variables from `LoopStep` are now saved and accessed with the symbol `%` instead of `$`
- 🚨 BREAKING CHANGE 🚨 function result are now saved and accessed with the symbol `%` instead of `$`, and the save key is provided by the user
- 🚨 BREAKING CHANGE 🚨 account's addresses can no longer be accessed with "[<account_id>]"
- `Scenes` have now default values for allowed scenarios and allowed networks
- 🚨 BREAKING CHANGE 🚨 removed analyze feature from MxOps
- 🚨 BREAKING CHANGE 🚨 rework the data save structure and introduce versioned data structure
- 🚨 BREAKING CHANGE 🚨 upgrade to the new multiversx-sdk-py 1.0.0 and removal of MxPySerializer
- 🚨 BREAKING CHANGE 🚨 OptionalValue are mandatory now (user must input "null")
- 🚨 BREAKING CHANGE 🚨 Enums format has changed to use the one from the multiversx-sdk-py
- 🚨 BREAKING CHANGE 🚨 MultiValueEncoded format has changed to use the one from the multiversx-sdk-py
- 🚨 BREAKING CHANGE 🚨 ledger account index was dropped as it is not used by multiversx-sdk-py
- upgraded all dependencies
- use uv instead of conda for development and env tests
- 🚨 BREAKING CHANGE 🚨 new class workflow for checks, smart-values and steps
- 🚨 BREAKING CHANGE 🚨 Accounts are now saved by bech32, the name to bech32 translation is done using the storage
- 🚨 BREAKING CHANGE 🚨 ABIS are now stored using a contract bech32
- 🚨 BREAKING CHANGE 🚨 Contracts are now handled using contract bech32 by the Scenario Data
- 🚨 BREAKING CHANGE 🚨 All accounts (user, contracts, internal, external) are now defined under the same "accounts" key in scenes
- use uv for package build
- 🚨 BREAKING CHANGE 🚨 scene_path attribute of SceneStep has been renamed path



## 2.2.0 - 2024-04-16

### Added

- `Scenario` clone command
- Allowed `TransfersCheck` to dynamically evaluate sender and receiver by name

### Fixed

- Updated the name 'local-testnet' to 'localnet'

## 2.1.0 - 2024-03-01

### Added

- ABI support for smart-contract
- Added new examples for queries

## 2.0.1 - 2023-10-25

### Fixed

- wrongly converted hex arguments
- broken ledger sign

## 2.0.0 - 2023-10-20

### Fixed

- Use of missing signer for LedgerAccount
- Missing parsing of hexadecimal value as string

### Added

- Checkpoints for `Scenario`
- `ContractUpgradeStep`
- Auto retry for empty query results
- python step class
- Value key can now of any depth for `Scenario` data
- `SceneStep`
- `analyze` module

### Changed

- 🚨 BREAKING CHANGE 🚨 `checks` attribute has been given for all `TransactionStep`, sometimes replacing `check_success`
- 🚨 BREAKING CHANGE 🚨 `.` and `[]` are used instead of `%` to specify a `Scenario` value key
- 🚨 BREAKING CHANGE 🚨 `data.data.py` renamed into `data.execution_data.py`
- Upgrade MultiversX python libraries
- `int` is preferred over `number` for query return type

### Fixed

- Bug with the `skip confirmation` CLI command
- Wrong token properties set during token registration

## 1.1.0 - 2023-05-11

### Added

- CLI options to clean/delete `Scenario` data before or after execution
- `Steps` for token transfers (eGLD, fungible & non fungible)
- `Steps` for token issuance, roles management and minting (fungible & non fungible)
- `TransfersCheck` to verify the transfers of a `ContractCallStep`
- Networks enumerations can be parsed by their short or full names

### Modified

- Switch integration tests contracts from elrond-wasm to multiversx-sc
- Add diverse precision on contribution

### Fixed

- Error when providing absolute path for `Scenes`
- Commit change when auto bumping changelog version
- Make the pylint test fail if a pylint error is detected

## 1.0.0 - 2023-03-09

### Added

- Check classes for `CallStep`
- External contract support for contract calls and queries (including results save)
- CI and script for bandit, flake8 and pylint
- CI for pytest tests
- CI for python package build
- CI for package publication on PYPI
- Wrapping example in the documentation

### Changed

- 🚨 BREAKING CHANGE 🚨 `contract_id` attribute renamed to `contract` for calls and queries
- 🚨 BREAKING CHANGE 🚨 Refactor check_for_errors attribute to be more general (allow more checks in the future)
- Reorganize integration tests folders, scripts and scenario names
- Convert the "Getting Started" section to a complete chapter in the documentation

## 0.1.1 - 2023-01-24

### Added

- Readthedocs yaml configuration file to fix compilation
- Full user tutorial in the sphinx documentation

## 0.1.0 - 2023-01-23

First version of MxOps.
