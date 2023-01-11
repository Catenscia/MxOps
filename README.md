# MvxOps

MvxOps is a python package to automate MultiversX smart contracts deployments and interactions in general.
These interactions are described by the user in one or several files (called scenes).
MvxOps also provide smart values: values used in the scenes (ex a token identifier) can be directly written in the file but also taken from the environment, from a config file or even from smart contract queries.

## Overview

A user write a scene which contains a number of steps. Each step represent an action: contract deployment, contract call, contract query.
(See Section Steps for more information).
The user can then execute the scene (or directly a folder of scenes) in a scenario.
A scenario is an environnement associated wich a chain (local, test, dev or main) in which contract data is recorded. (more on that in the [Scenario section](#scenario))

## Details

### Config

### Scenario

This allows you to have several instances of the same contract on the same chain.

### Scenes

### Steps

#### Contract Deployment Step

This step is used to specify a contract deployment.

#### Contract Call Step

This step is used to specify a contract call.

#### Contract Query Step

This step is used to specify a contract query.

### Smart Values

What makes MvxOps truly usefull is its ability to use smart values in the contract steps. Smart-values can be taken from the environment variables, from the config file of your project or from the results of smart_contract-queries.

#### Environment Smart Values

exemple

#### Config Smart Values

exemple

#### Contract Query Smart Values

exemple

## Backlog

- [ ] Add an optional delay before/after each step
- [ ] Create a framework to allow a user to create a step which will execute any custom made python functions. (This would allow extreme customizations for users)
- [x] Add Ledger support
- [ ] Add Keystore support
- [ ] Add Maiar support
- [ ] Add a specific step for contract ownership transfer.
- [ ] Add a skip keyword to skip steps without deleting them
- [ ] Out of gas transaction error
- [ ] Add querry support for external contracts
- [ ] Refactor scene files format to extract conditions and accounts
