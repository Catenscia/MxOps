# Analyze

`Mxops Analyze` is an entire module that aims to give you insights on the usage of your contracts, be it after a long period of tests or during the contracts' lives on the mainnet.

## Data

First, MxOps needs to fetch the transactions of your contract. You can either give the bech32 address of the contract or the name and scenario of your contract if you deployed it using MxOps.

### Commands

```bash
mxops analyze update-tx -n mainnet -c erd1qqqqqqqqqqqqqpgqqff57a6l7ztsrk45k9grjs4npvla9jyktnqqhmwngx
```

or 

```bash
mxops analyze update-tx -n mainnet -s my_scenario -c my_contract_name
```

This will save the transactions locally on your computer, so you won't have to download them each time you want to analyze your contract.

```{note}
Only users transactions are fetched. That is to say, only the transactions emitted by a user directly to your contract. All smart-contract to smart-contract calls are not retrieved.
```

### Rate limits

The APIs provided publicly by the MultiversX team have limits rates, so if you have a lots of transactions to analyze, it can take a lot of time to fetch all of them.

If you have your own API, you can dump the MxOps config by using `mxops config -d` and then modify the values `API` and `API_RATE_LIMIT`. This will automatically be taken into account in your next execution. (as long as you don't change of current working directory)

## Plots

Once your data is available, you can create plots to gain insights on your contract utilization.

```bash
mxops analyze plots -n mainnet -s my_scenario -c my_contract_name <plot_1> <plot_2>
```

or

```bash
mxops analyze plots -n mainnet -c erd1qqqqqqqqqqqqqpgqqff57a6l7ztsrk45k9grjs4npvla9jyktnqqhmwngx <plot_1> <plot_2>
```

### Available plots

Many more plots will be added in future versions

#### functions_per_day

```{thumbnail} ../images/functions_per_day.png
```

#### transactions_status_per_day

```{thumbnail} ../images/transactions_status_per_day.png
```

#### unique_users_per_day

```{thumbnail} ../images/unique_users_per_day.png
```