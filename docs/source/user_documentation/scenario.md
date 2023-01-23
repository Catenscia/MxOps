# Scenario

`Scenario` are an environment in which the results of the every `step` execution will be stored locally on your computer. This allows to execute identical `Scenes` on different contracts in the **same** network and it is also essential to use these results at a later time (for example to upgrade a contract).

An important think to keep in mind is that `Scenario` data is save on a user level. The current directory does not affect the `Scenario` behavior. This means that `Scenario` can be access from anywhere on your computer (which is usefull) bu also that their name should be unique for all your projects.

## Commands

Scenario can be accessed through the `data` command of MxOps.
Below sections show some command examples. You can always use `mxops data --help` to get more information.

### Existing Scenario

To print out all the existing scenario on a specified network:

```bash
mxops data get -n <NETWORK> -l
```

### Scenario Data

To print out all the existing data for a scenario on a specified network:

```bash
mxops data get -n <NETWORK> -s <scenario>
```

### Delete Scenario

To delete all the data from a scenario

```bash
mxops data delete -n <NETWORK> -s <scenario>
```
