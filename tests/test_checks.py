import json
from pathlib import Path

from multiversx_sdk_network_providers.transactions import TransactionOnNetwork
from mxops.execution.checks import TransfersCheck

from mxops.execution.msc import ExpectedTransfer, OnChainTransfer


def test_transfers_equality():
    # Given
    expected_transfers = [
        ExpectedTransfer('A', 'B', 'tokenA', '15'),
        ExpectedTransfer('A', 'B', 'tokenA', '18'),
        ExpectedTransfer('C', 'B', 'tokenA', '15'),
        ExpectedTransfer('A', 'D', 'tokenA', '15'),
    ]

    onchain_transfers = [
        OnChainTransfer('A', 'B', 'tokenA', '15'),
        OnChainTransfer('A', 'B', 'tokenA', '18'),
        OnChainTransfer('C', 'B', 'tokenA', '15'),
        OnChainTransfer('A', 'D', 'tokenA', '15'),
    ]

    # When
    # Then
    for et, ot in zip(expected_transfers, onchain_transfers):
        assert et == ot
        assert ot == et
        assert et in onchain_transfers
        assert ot in expected_transfers

    for i in range(len(expected_transfers)):
        for j in range(i+1, len(expected_transfers)):
            assert expected_transfers[i] != expected_transfers[j]
            assert onchain_transfers[i] != onchain_transfers[j]

    assert expected_transfers == onchain_transfers


def test_exact_add_liquidity_transfers_check(test_data_folder_path: Path):
    # Given
    with open(test_data_folder_path / 'api_responses' / 'add_liquidity.json') as file:
        onchain_tx = TransactionOnNetwork.from_proxy_http_response(**json.load(file))

    expected_transfers = [
        ExpectedTransfer(
            'erd1n775edthxhyrhntcutmqfspanmjvscumxuydmm83xumlahz75kfsgp62ss',
            'erd1qqqqqqqqqqqqqpgqav09xenkuqsdyeyy5evqyhuusvu4gl3t2jpss57g8x',
            'WEGLD-bd4d79',
            '2662383390769244262'),
        ExpectedTransfer(
            'erd1n775edthxhyrhntcutmqfspanmjvscumxuydmm83xumlahz75kfsgp62ss',
            'erd1qqqqqqqqqqqqqpgqav09xenkuqsdyeyy5evqyhuusvu4gl3t2jpss57g8x',
            'RIDE-7d18e9',
            '1931527217545745197301'),
        ExpectedTransfer(
            'erd1qqqqqqqqqqqqqpgqav09xenkuqsdyeyy5evqyhuusvu4gl3t2jpss57g8x',
            'erd1n775edthxhyrhntcutmqfspanmjvscumxuydmm83xumlahz75kfsgp62ss',
            'EGLDRIDE-7bd51a',
            '1224365948567992620'),
        ExpectedTransfer(
            'erd1qqqqqqqqqqqqqpgqav09xenkuqsdyeyy5evqyhuusvu4gl3t2jpss57g8x',
            'erd1n775edthxhyrhntcutmqfspanmjvscumxuydmm83xumlahz75kfsgp62ss',
            'RIDE-7d18e9',
            '37'),
    ]

    # When
    transfer_check = TransfersCheck(expected_transfers, condition='exact')
    exact_result = transfer_check.get_check_status(onchain_tx)

    transfer_check = TransfersCheck(expected_transfers, condition='included')
    include_result = transfer_check.get_check_status(onchain_tx)

    transfer_check = TransfersCheck(expected_transfers, condition='exact', include_gas_refund=True)
    refund_result = transfer_check.get_check_status(onchain_tx)

    transfer_check = TransfersCheck(
        expected_transfers,
        condition='included',
        include_gas_refund=True
    )
    included_refund_result = transfer_check.get_check_status(onchain_tx)

    # Then
    assert exact_result
    assert include_result
    assert not refund_result
    assert included_refund_result
