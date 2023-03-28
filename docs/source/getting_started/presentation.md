# MxOps Presentation

MxOps is a python package created to automate MultiversX smart contracts deployments, calls and queries.
Inspired from DevOps tools, it aims to ease and make reproducible any set of these interactions with smart-contracts.

MxOps aims to be useful in these situations:

- deployment automation
- on-chain integration tests
- contract interaction automation

## User Flow

MxOps works with simple yaml files called `Scenes`. In these `Scenes` you will simply describe the different elements that will be used to interact with your smart-contracts.
During execution, MxOps will save two types of data locally on you computer:

- deployment addresses for new contracts
- query results (only when specified)

This data is accessible to MxOps and can be reused within `Scenes`.

Here is a little illustration of what is happening (click on it to zoom-in):

```{thumbnail} ../images/mxops_illustration.svg
```

If you are a bit confused by this illustration, don't worry: the only thing you will have to do is to write `Scenes` and execute them. Next paragraph gives you a broad understanding of the constitution of a `Scene`.

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
    - "deploy_stake_withdraw"

  accounts:
    - account_name: owner
      pem_path: "./wallets/my_devnet_wallet.pem"

  steps:
    - type: ContractDeploy
      sender: owner
      wasm_path: "./contracts/my_contract.wasm"
      contract_id: "my-contract"
      gas_limit: 50000000
      upgradeable: True
      readable: False
      payable: False
      payable_by_sc: True

    - type: ContractCall
      sender: owner
      contract: "my-contract"
      endpoint: stake
      gas_limit: 100000000
      value: 50000000000000000
    
    - type: ContractQuery
      contract: "my-contract"
      endpoint: getStakedAmount
      arguments:
          - "[owner]"
      expected_results:
        - save_key: ownerStakedAmount
          result_type: number

    - type: ContractCall
      sender: owner
      contract: "my-contract"
      endpoint: withdraw
      gas_limit: 5000000
      arguments:
        - "%my-contract%ownerStakedAmount"

  ```

A lot of information is written here, but you don't have to worry about the details for now. Just remember that `Scenes` are the core of `MxOps` and that it tells the program what to do.

You will be guided through the steps of writing a `Scene` in the next sections. But before that, you need to 🚧 {doc}`install MxOps! <installation>` 🚧
