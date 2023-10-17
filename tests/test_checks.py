import json
from pathlib import Path

from multiversx_sdk_cli.accounts import Account, Address
from multiversx_sdk_network_providers.transactions import TransactionOnNetwork

from mxops.data.execution_data import InternalContractData, ScenarioData
from mxops.errors import CheckFailed
from mxops.execution.account import AccountsManager
from mxops.execution.checks import TransfersCheck
from mxops.execution.msc import ExpectedTransfer, OnChainTransfer


def test_transfers_equality():
    # Given
    expected_transfers = [
        ExpectedTransfer("A", "B", "tokenA", "15"),
        ExpectedTransfer("A", "B", "tokenA", "18"),
        ExpectedTransfer("C", "B", "tokenA", "15"),
        ExpectedTransfer("A", "D", "tokenA", 15),
        ExpectedTransfer("A", "D", "MyNFT", 1, nonce=3661),
        ExpectedTransfer("A", "D", "MySFT", 15848, nonce=210),
    ]

    onchain_transfers = [
        OnChainTransfer("A", "B", "tokenA", "15"),
        OnChainTransfer("A", "B", "tokenA", "18"),
        OnChainTransfer("C", "B", "tokenA", "15"),
        OnChainTransfer("A", "D", "tokenA", "15"),
        OnChainTransfer("A", "D", "MyNFT-0e4d", "1"),
        OnChainTransfer("A", "D", "MySFT-d2", "15848"),
    ]

    # When
    # Then
    for et, ot in zip(expected_transfers, onchain_transfers):
        assert et == ot
        assert ot == et
        assert et in onchain_transfers
        assert ot in expected_transfers

    for i in range(len(expected_transfers)):
        for j in range(i + 1, len(expected_transfers)):
            assert expected_transfers[i] != expected_transfers[j]
            assert onchain_transfers[i] != onchain_transfers[j]

    assert expected_transfers == onchain_transfers


def test_data_load_equality():
    # Given
    AccountsManager._accounts["owner"] = Account(
        Address.from_bech32(
            "erd1zzugxvypryhfym7qrnnkxvrlh8d9ylw2s0399q5tzp43g297plcq4p6d30"
        )
    )
    scenario = ScenarioData.get()
    contract_data = InternalContractData(
        contract_id="egld-ping-pong",
        address="erd1qqqqqqqqqqqqqpgqpxkd9qgyyxykq5l6d8v9zud99hpwh7l0plcq3dae77",
        saved_values={"PingAmount": 1000000000000000000},
        wasm_hash="1383133d22b8be01c4dc6dfda448dbf0b70ba1acb348a50dd3224b9c8bb21757",
        deploy_time=1677261606,
        last_upgrade_time=1677261606,
    )
    scenario.add_contract_data(contract_data)

    expected_transfer = ExpectedTransfer(
        sender="[owner]",
        receiver="%egld-ping-pong.address",
        token_identifier="EGLD",
        amount="%egld-ping-pong.PingAmount",
    )

    on_chain_transfers = [
        OnChainTransfer(
            sender="erd1zzugxvypryhfym7qrnnkxvrlh8d9ylw2s0399q5tzp43g297plcq4p6d30",
            receiver="erd1qqqqqqqqqqqqqpgqpxkd9qgyyxykq5l6d8v9zud99hpwh7l0plcq3dae77",
            token_identifier="EGLD",
            amount="1000000000000000000",
        )
    ]

    # When
    index = on_chain_transfers.index(expected_transfer)

    # Then
    assert index == 0


def test_exact_add_liquidity_transfers_check(test_data_folder_path: Path):
    # Given
    with open(test_data_folder_path / "api_responses" / "add_liquidity.json") as file:
        onchain_tx = TransactionOnNetwork.from_proxy_http_response(**json.load(file))

    expected_transfers = [
        ExpectedTransfer(
            "erd1n775edthxhyrhntcutmqfspanmjvscumxuydmm83xumlahz75kfsgp62ss",
            "erd1qqqqqqqqqqqqqpgqav09xenkuqsdyeyy5evqyhuusvu4gl3t2jpss57g8x",
            "WEGLD-bd4d79",
            "2662383390769244262",
        ),
        ExpectedTransfer(
            "erd1n775edthxhyrhntcutmqfspanmjvscumxuydmm83xumlahz75kfsgp62ss",
            "erd1qqqqqqqqqqqqqpgqav09xenkuqsdyeyy5evqyhuusvu4gl3t2jpss57g8x",
            "RIDE-7d18e9",
            "1931527217545745197301",
        ),
        ExpectedTransfer(
            "erd1qqqqqqqqqqqqqpgqav09xenkuqsdyeyy5evqyhuusvu4gl3t2jpss57g8x",
            "erd1n775edthxhyrhntcutmqfspanmjvscumxuydmm83xumlahz75kfsgp62ss",
            "EGLDRIDE-7bd51a",
            "1224365948567992620",
        ),
        ExpectedTransfer(
            "erd1qqqqqqqqqqqqqpgqav09xenkuqsdyeyy5evqyhuusvu4gl3t2jpss57g8x",
            "erd1n775edthxhyrhntcutmqfspanmjvscumxuydmm83xumlahz75kfsgp62ss",
            "RIDE-7d18e9",
            "37",
        ),
    ]

    # When
    transfer_check = TransfersCheck(expected_transfers, condition="exact")
    exact_result = transfer_check.get_check_status(onchain_tx)

    transfer_check = TransfersCheck(expected_transfers, condition="included")
    include_result = transfer_check.get_check_status(onchain_tx)

    transfer_check = TransfersCheck(
        expected_transfers, condition="exact", include_gas_refund=True
    )
    refund_result = transfer_check.get_check_status(onchain_tx)
    try:
        transfer_check.raise_on_failure(onchain_tx)
        raise RuntimeError("Above line should raise an error")
    except CheckFailed:
        pass

    transfer_check = TransfersCheck(
        expected_transfers, condition="included", include_gas_refund=True
    )
    included_refund_result = transfer_check.get_check_status(onchain_tx)

    # Then
    assert exact_result
    assert include_result
    assert not refund_result
    assert included_refund_result
