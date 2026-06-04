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

## Block generation

By default, the chain-simulator does not produce blocks on its own: MxOps drives
block production for you. After sending a transaction it asks the simulator to
generate blocks until the transaction is processed, and steps like `Wait` with
`for_blocks` generate the requested blocks directly.

The chain-simulator can also be configured (via its own `config.toml`) to
auto-generate blocks at a fixed interval, behaving like a real network. There is
no endpoint to detect this mode, so MxOps exposes a config option to control it:

```ini
[CHAIN_SIMULATOR]
AUTO_GENERATE_BLOCKS=true
```

- `true` (default): MxOps generates blocks itself (the behavior described above).
- `false`: MxOps does not generate any block and simply waits for the simulator
  to produce them on its own, exactly like on devnet or mainnet. Set this when
  you point MxOps at a simulator started with `auto-generate-blocks` enabled.

This option only applies to the chain-simulator network and has no effect on
other networks.

You can also toggle this option mid-scene with the
[Set Config step](set_config_step_target), for example to run fast
MxOps-driven setup steps and then switch to `AUTO_GENERATE_BLOCKS=false` so the
rest of the scene relies on the simulator's own block production.
