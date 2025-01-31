from pathlib import Path

from multiversx_sdk import Account

from mxops.data.execution_data import InternalContractData, ScenarioData
from mxops.execution.account import AccountsManager
from mxops.execution.legacy_msc import ExpectedTransfer, OnChainTransfer


def test_transfers_equality():
    # Given
    expected_transfers = [
        ExpectedTransfer(
            "%test_user_A.address",
            "my_test_contract",
            "tokenA",
            "15",
        ),
        ExpectedTransfer(
            "erd1yy995sn9drrlj7qvzgpcyfgexl7kh9u33l3zqp5np20vw5p2jmwq7s4ark",
            "%my_test_contract.address",
            "tokenA",
            "18",
        ),
        ExpectedTransfer(
            "my_test_contract",
            "[test_user_A]",
            "tokenA",
            "15",
        ),
        ExpectedTransfer(
            "%my_test_contract.address",
            "%test_user_B.address",
            "tokenA",
            15,
        ),
        ExpectedTransfer(
            "test_user_A",
            "erd1czt3wrd9qfsgqyfrgk9p48ug38s7qnlzqvvaquqcaz07wlk0dwnspwn7x0",
            "MyNFT",
            1,
            nonce=3661,
        ),
        ExpectedTransfer(
            "erd1yy995sn9drrlj7qvzgpcyfgexl7kh9u33l3zqp5np20vw5p2jmwq7s4ark",
            "erd1czt3wrd9qfsgqyfrgk9p48ug38s7qnlzqvvaquqcaz07wlk0dwnspwn7x0",
            "MySFT",
            15848,
            nonce=210,
        ),
    ]

    onchain_transfers = [
        OnChainTransfer(
            "erd1jzw34pun678ktsstunk0dm0z2uh7m0ld9trw507ksnzt0wxalwwsv3fpa2",
            "erd1qqqqqqqqqqqqqpgqdmq43snzxutandvqefxgj89r6fh528v9dwnswvgq9t",
            "tokenA",
            "15",
        ),
        OnChainTransfer(
            "erd1yy995sn9drrlj7qvzgpcyfgexl7kh9u33l3zqp5np20vw5p2jmwq7s4ark",
            "erd1qqqqqqqqqqqqqpgqdmq43snzxutandvqefxgj89r6fh528v9dwnswvgq9t",
            "tokenA",
            "18",
        ),
        OnChainTransfer(
            "erd1qqqqqqqqqqqqqpgqdmq43snzxutandvqefxgj89r6fh528v9dwnswvgq9t",
            "erd1jzw34pun678ktsstunk0dm0z2uh7m0ld9trw507ksnzt0wxalwwsv3fpa2",
            "tokenA",
            "15",
        ),
        OnChainTransfer(
            "erd1qqqqqqqqqqqqqpgqdmq43snzxutandvqefxgj89r6fh528v9dwnswvgq9t",
            "erd1y3296u7m2v5653pddey3p7l5zacqmsgqc7vsu3w74p9jm2qp3tqqz950yl",
            "tokenA",
            "15",
        ),
        OnChainTransfer(
            "erd1jzw34pun678ktsstunk0dm0z2uh7m0ld9trw507ksnzt0wxalwwsv3fpa2",
            "erd1czt3wrd9qfsgqyfrgk9p48ug38s7qnlzqvvaquqcaz07wlk0dwnspwn7x0",
            "MyNFT-0e4d",
            "1",
        ),
        OnChainTransfer(
            "erd1yy995sn9drrlj7qvzgpcyfgexl7kh9u33l3zqp5np20vw5p2jmwq7s4ark",
            "erd1czt3wrd9qfsgqyfrgk9p48ug38s7qnlzqvvaquqcaz07wlk0dwnspwn7x0",
            "MySFT-d2",
            "15848",
        ),
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
    AccountsManager.register_account(
        "owner",
        Account.new_from_pem(Path("./tests/data/wallets_folder/alice.pem")),
    )
    scenario = ScenarioData.get()
    contract_data = InternalContractData(
        contract_id="egld-ping-pong-legacy",
        address="erd1qqqqqqqqqqqqqpgqpxkd9qgyyxykq5l6d8v9zud99hpwh7l0plcq3dae77",
        saved_values={"PingAmount": 1000000000000000000},
        wasm_hash="1383133d22b8be01c4dc6dfda448dbf0b70ba1acb348a50dd3224b9c8bb21757",
        deploy_time=1677261606,
        last_upgrade_time=1677261606,
    )
    scenario.add_contract_data(contract_data)

    expected_transfer = ExpectedTransfer(
        sender="%owner.address",
        receiver="%egld-ping-pong-legacy.address",
        token_identifier="EGLD",
        amount="%egld-ping-pong-legacy.PingAmount",
    )

    on_chain_transfers = [
        OnChainTransfer(
            sender="erd1pqslfwszea4hrxdvluhr0v7dhgdfwv6ma70xef79vruwnl7uwkdsyg4xj3",
            receiver="erd1qqqqqqqqqqqqqpgqpxkd9qgyyxykq5l6d8v9zud99hpwh7l0plcq3dae77",
            token_identifier="EGLD",
            amount="1000000000000000000",
        )
    ]

    # When
    index = on_chain_transfers.index(expected_transfer)

    # Then
    assert index == 0
