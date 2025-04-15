from multiversx_sdk import Address
import pytest_mock
from mxops.execution.scene import parse_load_account
from mxops.execution.steps import TransferStep


def test_egld_transfer():
    # Given
    step = TransferStep(
        sender="erd19dw6qeqyvn5ft7rqfzcds587j6u26n88kwkp0n0unnz7h2h6ds8qfpjmch",
        receiver="erd1qqqqqqqqqqqqqqqpqqqqqqqqqqqqqqqqqqqqqqqqqqqqqxhllllssz7sl7",
        value=123456,
    )

    # When
    step.evaluate_smart_values()
    tx = step.build_unsigned_transaction()

    # Then
    assert (
        tx.sender.to_bech32()
        == "erd19dw6qeqyvn5ft7rqfzcds587j6u26n88kwkp0n0unnz7h2h6ds8qfpjmch"
    )
    assert (
        tx.receiver.to_bech32()
        == "erd1qqqqqqqqqqqqqqqpqqqqqqqqqqqqqqqqqqqqqqqqqqqqqxhllllssz7sl7"
    )
    assert tx.value == 123456
    assert tx.data == b""


def test_simple_esdt_transfer():
    # Given
    step = TransferStep(
        sender="erd19dw6qeqyvn5ft7rqfzcds587j6u26n88kwkp0n0unnz7h2h6ds8qfpjmch",
        receiver="erd1qqqqqqqqqqqqqqqpqqqqqqqqqqqqqqqqqqqqqqqqqqqqqxhllllssz7sl7",
        transfers=[["WEGLD-abcdef", 10]],
    )

    # When
    step.evaluate_smart_values()
    tx = step.build_unsigned_transaction()

    # Then
    assert (
        tx.sender.to_bech32()
        == "erd19dw6qeqyvn5ft7rqfzcds587j6u26n88kwkp0n0unnz7h2h6ds8qfpjmch"
    )
    assert (
        tx.receiver.to_bech32()
        == "erd1qqqqqqqqqqqqqqqpqqqqqqqqqqqqqqqqqqqqqqqqqqqqqxhllllssz7sl7"
    )
    assert tx.value == 0
    assert tx.data == b"ESDTTransfer@5745474c442d616263646566@0a"


def test_multi_esdt_transfer():
    # Given
    step = TransferStep(
        sender="erd19dw6qeqyvn5ft7rqfzcds587j6u26n88kwkp0n0unnz7h2h6ds8qfpjmch",
        receiver="erd1qqqqqqqqqqqqqqqpqqqqqqqqqqqqqqqqqqqqqqqqqqqqqxhllllssz7sl7",
        transfers=[
            ["WEGLD-abcdef", 10],
            {"identifier": "NFT-abcdef", "nonce": 12, "amount": 1},
        ],
    )

    # When
    step.evaluate_smart_values()
    tx = step.build_unsigned_transaction()

    # Then
    assert (
        tx.sender.to_bech32()
        == "erd19dw6qeqyvn5ft7rqfzcds587j6u26n88kwkp0n0unnz7h2h6ds8qfpjmch"
    )
    assert (
        tx.receiver.to_bech32()
        == "erd19dw6qeqyvn5ft7rqfzcds587j6u26n88kwkp0n0unnz7h2h6ds8qfpjmch"
    )
    assert tx.value == 0
    assert tx.data == (
        b"MultiESDTNFTTransfer@0000000000000000000100000000000000000000000000000000000"
        b"01affffff@02@5745474c442d616263646566@@0a@4e46542d616263646566@0c@01"
    )


def test_simple_esdt_transfer_with_egld():
    # Given
    step = TransferStep(
        sender="erd19dw6qeqyvn5ft7rqfzcds587j6u26n88kwkp0n0unnz7h2h6ds8qfpjmch",
        receiver="erd1qqqqqqqqqqqqqqqpqqqqqqqqqqqqqqqqqqqqqqqqqqqqqxhllllssz7sl7",
        transfers=[["WEGLD-abcdef", 10]],
        value=10,
    )

    # When
    step.evaluate_smart_values()
    tx = step.build_unsigned_transaction()

    # Then
    assert (
        tx.sender.to_bech32()
        == "erd19dw6qeqyvn5ft7rqfzcds587j6u26n88kwkp0n0unnz7h2h6ds8qfpjmch"
    )
    assert (
        tx.receiver.to_bech32()
        == "erd19dw6qeqyvn5ft7rqfzcds587j6u26n88kwkp0n0unnz7h2h6ds8qfpjmch"
    )
    assert tx.value == 0
    assert tx.data == (
        b"MultiESDTNFTTransfer@0000000000000000000100000000000000000000000000000000000"
        b"01affffff@02@5745474c442d616263646566@@0a@45474c442d303030303030@@0a"
    )


def test_ledger_tx_sign(mocker: pytest_mock.MockerFixture):
    # Given
    mock_bech32 = "erd1spyavw0956vq68xj8y4tenjpq2wd5a9p2c6j8gsz7ztyrnpxrruqzu66jx"
    account_id = "my_ledger_account"
    raw_account = {"account_id": account_id, "ledger_address_index": 0}
    mocker.patch(
        "multiversx_sdk.accounts.ledger_account.LedgerAccount._get_address",
        side_effect=lambda: Address.new_from_bech32(mock_bech32),
    )
    mocker.patch("multiversx_sdk.accounts.ledger_account.LedgerApp.set_address")
    mocker.patch("ledgercomm.Transport")
    parse_load_account(raw_account)

    step = TransferStep(
        sender="my_ledger_account",
        receiver="my_ledger_account",
        value=123456,
        checks=[],
    )

    mocker.patch(
        "mxops.execution.steps.base.send", side_effect=lambda *args: "fake_hash"
    )
    mocker.patch(
        "multiversx_sdk.accounts.ledger_account.LedgerApp.sign_transaction",
        side_effect=lambda *args: b"fake_sig".hex(),
    )

    # When / Then
    # check that the option has well been set when signing with a ledger account
    # the multiversx sdk would throw an error otherwise
    step.execute()
