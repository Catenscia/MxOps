# Transaction Checks

When executing a `Step` that send a blockchain transaction, you may want to assert that everything went as you desired.
MxOps provides you a way to do so: `Checks` are additional information you can provide when
declaring a `Step`.

If any of the `Checks` you specified is not successful, it will stop the execution of MxOps
and raise an error.

At the moment, only two types of `Checks` exists: `SuccessCheck` and `TransfersCheck`. We plan
on adding more types in the future such as `BalanceCheck`, `ErrorCheck`,
`StorageCheck` and much more.

## SuccessCheck

This is the most simple `Check` and is included by default on every transaction `Step`. This will verify
that the transaction went without any error.

If you use the `checks` keywords, make sure to add the `SuccessCheck` like this:

```yaml
type: ContractCall
sender: alice
contract: my_first_sc
endpoint: myEndpoint
gas_limit: 60000000
arguments:
  - arg1
value: 0
checks:
  - type: Success
```

In some cases, you may want to send many transactions quickly, without checking their results.
If you declare no `Checks`, MxOps will send the transaction without waiting for the result,
gaining a significant time.

```yaml
type: ContractCall
sender: alice
contract: my_first_sc
endpoint: myEndpoint
gas_limit: 60000000
arguments:
  - arg1
value: 0
checks: []
```

## TransfersCheck

This class allows you to verify the token transfers that have been made during a transaction. This
is very useful to assert the behavior of any smart-contract that is dealing with tokens.

For example, let's say the user `alice` call a smart-contract named `super-swap-sc` to sell in one
transaction some classic ESDT and some Meta ESDT. She expects the contract to send her eGLD
in exchange.

```yaml
type: ContractCall
sender: alice
contract: super-swap-sc
endpoint: superSell
gas_limit: 60000000
esdt_transfers:
  - token_identifier: ALICE-123456
    amount: 58411548
    nonce: 0
  - token_identifier: XMEX-e45d41
    amount: 848491898
    nonce: 721
checks:
  - type: Success

  - type: Transfers
    condition: exact
    include_gas_refund: false # optional, false by default
    expected_transfers:
      - sender: "alice"
        receiver: "super-swap-sc"
        token_identifier: ALICE-123456
        amount: 58411548
      - sender: "alice"
        receiver: "super-swap-sc"
        token_identifier: XMEX-e45d41
        amount: 848491898
        nonce: 721 # can write 721 as integer or "0d21" for its hex representation
      - sender: "super-swap-sc"
        receiver: "alice"
        token_identifier: EGLD
        amount: 18541
```

If we only want to check that we received back the EGLD, we can use the value `included` for the
`condition` attribute. This tells MxOps to only look if the specified expected transfers are
included in the on-chain transaction.

```yaml
type: ContractCall
sender: alice
contract: super-swap-sc
endpoint: superSell
gas_limit: 60000000
esdt_transfers:
  - token_identifier: ALICE-123456
    amount: 58411548
    nonce: 0
  - token_identifier: XMEX-e45d41
    amount: 848491898
    nonce: 721
checks:
  - type: Success

  - type: Transfers
    condition: included
    expected_transfers:
      - sender: "%super-swap-sc.address"
        receiver: "%alice.address"
        token_identifier: EGLD
        amount: 18541
```
