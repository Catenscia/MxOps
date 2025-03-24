import json
from pathlib import Path
import re

from multiversx_sdk import Address, Token
from multiversx_sdk.network_providers.http_resources import (
    transaction_from_proxy_response,
)
import pytest

from mxops.data.execution_data import InternalContractData, ScenarioData
from mxops.errors import CheckFailed
from mxops.execution.checks import SuccessCheck, TransfersCheck
from mxops.execution.msc import OnChainTokenTransfer
from mxops.smart_values import SmartOnChainTokenTransfer


def test_onchain_and_expected_transfer_equality():
    # Given
    scenario = ScenarioData.get()
    contract_data = InternalContractData(
        account_id="egld-ping-pong",
        bech32="erd1qqqqqqqqqqqqqpgqpxkd9qgyyxykq5l6d8v9zud99hpwh7l0plcq3dae77",
        saved_values={"PingAmount": 1000000000000000000},
        code_hash="1383133d22b8be01c4dc6dfda448dbf0b70ba1acb348a50dd3224b9c8bb21757",
        deploy_time=1677261606,
        last_upgrade_time=1677261606,
    )
    scenario.add_account_data(contract_data)

    expected_transfer = SmartOnChainTokenTransfer(
        {
            "sender": "alice",
            "receiver": "%egld-ping-pong.address",
            "token_identifier": "EGLD",
            "amount": "%egld-ping-pong.PingAmount",
        }
    )

    on_chain_transfers = [
        OnChainTokenTransfer(
            sender=Address.new_from_bech32(
                "erd1pqslfwszea4hrxdvluhr0v7dhgdfwv6ma70xef79vruwnl7uwkdsyg4xj3"
            ),
            receiver=Address.new_from_bech32(
                "erd1qqqqqqqqqqqqqpgqpxkd9qgyyxykq5l6d8v9zud99hpwh7l0plcq3dae77"
            ),
            token=Token("EGLD"),
            amount=1000000000000000000,
        )
    ]

    # When
    expected_transfer.evaluate()
    index = on_chain_transfers.index(expected_transfer.get_evaluated_value())

    # Then
    assert index == 0


def test_add_liquidity_transfers_check(test_data_folder_path: Path):
    # Given
    with open(test_data_folder_path / "api_responses" / "add_liquidity.json") as file:
        onchain_tx = transaction_from_proxy_response(**json.load(file))

    expected_transfers = [
        [
            "erd1n775edthxhyrhntcutmqfspanmjvscumxuydmm83xumlahz75kfsgp62ss",
            "erd1qqqqqqqqqqqqqpgqav09xenkuqsdyeyy5evqyhuusvu4gl3t2jpss57g8x",
            "WEGLD-bd4d79",
            "2662383390769244262",
        ],
        [
            "erd1n775edthxhyrhntcutmqfspanmjvscumxuydmm83xumlahz75kfsgp62ss",
            "erd1qqqqqqqqqqqqqpgqav09xenkuqsdyeyy5evqyhuusvu4gl3t2jpss57g8x",
            "RIDE-7d18e9",
            "1931527217545745197301",
        ],
        [
            "erd1qqqqqqqqqqqqqpgqav09xenkuqsdyeyy5evqyhuusvu4gl3t2jpss57g8x",
            "erd1n775edthxhyrhntcutmqfspanmjvscumxuydmm83xumlahz75kfsgp62ss",
            "EGLDRIDE-7bd51a",
            "1224365948567992620",
        ],
        [
            "erd1qqqqqqqqqqqqqpgqav09xenkuqsdyeyy5evqyhuusvu4gl3t2jpss57g8x",
            "erd1n775edthxhyrhntcutmqfspanmjvscumxuydmm83xumlahz75kfsgp62ss",
            "RIDE-7d18e9",
            "37",
        ],
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
    with pytest.raises(CheckFailed, match=re.escape("Check failed on transaction")):
        transfer_check.raise_on_failure(onchain_tx)

    transfer_check = TransfersCheck(
        expected_transfers, condition="included", include_gas_refund=True
    )
    included_refund_result = transfer_check.get_check_status(onchain_tx)

    # Then
    assert exact_result
    assert include_result
    assert not refund_result
    assert included_refund_result


def test_success_check(test_data_folder_path: Path):
    # Given
    with open(test_data_folder_path / "api_responses" / "add_liquidity.json") as file:
        success_onchain_tx = transaction_from_proxy_response(**json.load(file))
    with open(test_data_folder_path / "api_responses" / "not_enough_esdt.json") as file:
        fail_onchain_tx = transaction_from_proxy_response(**json.load(file))

    # When
    check = SuccessCheck()
    result = check.get_check_status(success_onchain_tx)
    with pytest.raises(CheckFailed):
        SuccessCheck().raise_on_failure(fail_onchain_tx)

    # Then
    assert result
