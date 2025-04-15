# Chain-simulator

The chain simulator is exactly like mainnet blockchain, expect that there is no consensus and that you can generate blocks at will. It is the perfect setup for on-chain testing.
MxOps gives some command lines to quickly setup the chain-simulator on your computer.

MxOps relies on [this repository](https://github.com/multiversx/full-stack-docker-compose) from the MultiversX core team to setup the chain-simulator itself, but also a gateway, an API, an explorer and an elastic search instance.

## Requirements

You will need to have the following installed:

- MxOps: [installation steps](../getting_started/introduction)
- Docker: [installation steps](https://docs.docker.com/engine/install/)

## Start

Each time you start the chain-simulator, it is a completely new chain, all previous transactions you may have made in a previous session will be gone.
To start the chain-simulator, just enter the command below:

```bash
mxops chain-simulator start
```

You will see all the docker containers slowly getting started, and the first epoch on the chain will be automatically pre-generated.

```{note}
If you forgot to stop the chain-simulator last time you shutdown your computer, you might get some difficulty to access the explorer. In this case, stop the explorer and start it again.
```

## Stop

Once you are done, don't forget to stop the chain-simulator:


```bash
mxops chain-simulator stop
```
