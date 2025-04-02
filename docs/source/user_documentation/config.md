# Configuration File

MxOps relies on [configparser](https://docs.python.org/3/library/configparser.html) to handle configuration values. For example, this is used to set the chain ID depending on the network the user specified (mainnet, devnet ...).

## Configuration Initialization

When you execute MxOps, it will look for a configuration file by executing the following actions in this order:

- Look if a config file path is written in the environment variable `MXOPS_CONFIG`
- Otherwise look if a config file named `mxops_config.ini` exists in the current directory
- Else load the default config shipped with MxOps package

## Default Configuration

You can find the default configuration in the [github](https://github.com/Catenscia/MxOps/blob/main/mxops/resources/default_config.ini).

All values in the configuration are accessible in scene by using the "&" symbol. For example:

```yaml
steps:
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
```

See more info on this in the {doc}`values sections<values>`.

## Write Custom File

To write your custom config file, we recommend copying the default config and then you can add or modify all the values you need.
MxOps has a command to dump a copy of the default config:

```bash
mxops config -d
```

This will create a file name `mxops_config.ini` in your current working directory.
