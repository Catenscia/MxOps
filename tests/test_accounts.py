from mxops.data.execution_data import PemAccountData, ScenarioData
from mxops.execution.account import AccountsManager


def test_loaded_accounts():
    # Given
    scenario_data = ScenarioData.get()
    account_names = ["test_user_A", "test_user_B", "alice", "bob", "charlie"]
    expected_addresses = [
        "erd1jzw34pun678ktsstunk0dm0z2uh7m0ld9trw507ksnzt0wxalwwsv3fpa2",
        "erd1y3296u7m2v5653pddey3p7l5zacqmsgqc7vsu3w74p9jm2qp3tqqz950yl",
        "erd1pqslfwszea4hrxdvluhr0v7dhgdfwv6ma70xef79vruwnl7uwkdsyg4xj3",
        "erd1ddhla0htp9eknfjn628ut55qafcpxa9evxmps2aflq8ldgqq08esc3x3f8",
        "erd1jqtj976xg4fka5xqnt0e4vz4guh64x90jmr7csrjd3a55frvh9jqc2g9vg",
    ]

    # When
    accounts_manager = AccountsManager()
    loaded_accounts_addresses = [
        accounts_manager.get_account(name).address.to_bech32() for name in account_names
    ]
    loaded_accounts_addresses_from_data = [
        scenario_data.get_account_address(name).bech32() for name in account_names
    ]

    # Then
    assert set(accounts_manager._accounts.keys()) == set(expected_addresses)
    assert loaded_accounts_addresses == expected_addresses
    assert loaded_accounts_addresses_from_data == expected_addresses

    assert scenario_data.get_value("wallets_folder") == ["alice", "bob", "charlie"]


def test_account_data():
    # Given
    scenario_data = ScenarioData.get()
    # When
    address = scenario_data.get_account_address("alice")
    data = scenario_data.accounts_data[address.bech32()]

    # Then
    assert data == PemAccountData(
        "alice", address.to_bech32(), "tests/data/wallets_folder/alice.pem"
    )
