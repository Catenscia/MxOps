from multiversx_sdk import Account, Address, Transaction
import pytest
import pytest_mock
from mxops.data.execution_data import (
    AccountData,
    ExternalContractData,
    PemAccountData,
    ScenarioData,
)
from mxops.errors import UnknownAccount
from mxops.execution.account import AccountsManager
from mxops.execution.scene import parse_load_account
from mxops.execution.steps.transactions import TransferStep


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
        "alice", address.to_bech32(), "tests/data/wallets/folder_to_load/alice.pem"
    )


def test_reload_account():
    # Given
    scenario_data = ScenarioData.get()
    account_manager = AccountsManager()
    account_1_data = PemAccountData(
        "account_to_load_1",
        "erd18jhjjxjx9q8kud5kqap0xkddrw3fvzc5c60sx7aag2zk7afxw2zsqr3m3v",
        "tests/data/wallets/account_to_load_1.pem",
    )
    account_2_data = PemAccountData(
        "account_to_load_2",
        "erd1em7dlr8c3avclm6kq9kprag3sfe2pm4fjryfn0l8jj62l5ynmcqq4retvx",
        "tests/data/wallets/account_to_load_2.pem",
    )
    assert account_1_data.bech32 not in account_manager._accounts
    assert account_2_data.bech32 not in account_manager._accounts
    scenario_data.add_account_data(account_1_data)
    scenario_data.add_account_data(account_2_data)

    # When
    account_1 = account_manager.get_account(account_1_data.account_id)
    account_2 = account_manager.get_account(account_2_data.bech32)

    # Then
    assert account_1.address.to_bech32() == account_1_data.bech32
    assert account_2.address.to_bech32() == account_2_data.bech32


def test_unknown_account():
    # Given
    account_manager = AccountsManager()

    # When
    with pytest.raises(UnknownAccount):
        account_manager.get_account("unknown-account")


def test_ledger_loading(mocker: pytest_mock.MockerFixture):
    # Given
    mock_bech32 = "erd1spyavw0956vq68xj8y4tenjpq2wd5a9p2c6j8gsz7ztyrnpxrruqzu66jx"
    account_id = "my_ledger_account"
    raw_account = {"account_id": account_id, "ledger_address_index": 0}
    mocker.patch(
        "multiversx_sdk.accounts.ledger_account.LedgerAccount._get_address",
        side_effect=lambda: Address.new_from_bech32(mock_bech32),
    )

    # When
    parse_load_account(raw_account)
    account = AccountsManager.get_account(account_id)

    # Then
    assert account.address.to_bech32() == mock_bech32


def test_pem_account_loading():
    # Given
    account_id = "account_to_load_3"
    raw_account = {
        "pem_path": "tests/data/wallets/account_to_load_3.pem",
        "account_id": account_id,
    }

    # When
    parse_load_account(raw_account)
    account = AccountsManager.get_account(account_id)

    # Then
    assert (
        account.address.to_bech32()
        == "erd16t438r4hgjmg3gxp7mvk43jxrzkhrkr36lmwerd3rulw6yw9n5ms9jzeup"
    )


def test_folder_accounts_loading():
    # Given
    name = "wallets_folder"
    raw_account = {
        "name": name,
        "folder_path": "tests/data/wallets/folder_to_load",
    }

    # When
    parse_load_account(raw_account)

    # Then
    assert isinstance(AccountsManager.get_account("alice"), Account)
    assert isinstance(AccountsManager.get_account("bob"), Account)
    assert isinstance(AccountsManager.get_account("charlie"), Account)


def test_load_external_user():
    # Given
    account_id = "external_user"
    bech32 = "erd1f63dsctrvwaxxk04vll7ccl8wmza4aa5dk9maz36xdx8lkymq8cstac7yg"
    raw_account = {"account_id": account_id, "bech32": bech32}
    scenario_data = ScenarioData.get()

    # When
    parse_load_account(raw_account)
    account_data = scenario_data.get_account_data(account_id)

    # Then
    assert type(account_data) is AccountData
    assert account_data.account_id == account_id
    assert account_data.bech32 == bech32


def test_load_external_contract_with_contract_id():
    # Given
    account_id = "external_contract"
    bech32 = "erd1qqqqqqqqqqqqqpgq9ph6uhdl2hkq7sarxxwycr6txnx0ewcal3ts0cs79w"
    raw_account = {"contract_id": account_id, "bech32": bech32}
    scenario_data = ScenarioData.get()

    # When
    parse_load_account(raw_account)
    account_data = scenario_data.get_account_data(account_id)

    # Then
    assert type(account_data) is ExternalContractData
    assert account_data.account_id == account_id
    assert account_data.bech32 == bech32


def test_signature_ignore_unknown_account(chain_simulator_network):
    # Given

    transaction = Transaction(
        Address.from_bech32(
            "erd1q33a7f3wnq7l50hkh2t009z55v3dg8ksp3lr7xcafh0kknlgcteqkywxca"
        ),
        Address.from_bech32(
            "erd1q33a7f3wnq7l50hkh2t009z55v3dg8ksp3lr7xcafh0kknlgcteqkywxca"
        ),
        gas_limit=5000000,
        chain_id="D",
        nonce=1,
    )
    step = TransferStep(
        sender="erd1q33a7f3wnq7l50hkh2t009z55v3dg8ksp3lr7xcafh0kknlgcteqkywxca",
        receiver="erd1q33a7f3wnq7l50hkh2t009z55v3dg8ksp3lr7xcafh0kknlgcteqkywxca",
        value=1,
    )

    # When
    step.set_nonce_and_sign_transaction(transaction)

    # Then
    assert transaction.nonce == 1
    assert transaction.signature == b"aaaaa"


def test_signature_ignore_external_account(chain_simulator_network):
    # Given
    account_id = "external_signer"
    bech32 = "erd1muw5taleu9cejz5mhknan45yxmu0w8qxy7awps3w7fv5d8a0mz9sr90j0l"
    parse_load_account({"account_id": account_id, "bech32": bech32})

    transaction = Transaction(
        Address.from_bech32(bech32),
        Address.from_bech32(bech32),
        gas_limit=5000000,
        chain_id="D",
        nonce=1,
    )
    step = TransferStep(
        sender=bech32,
        receiver=bech32,
        value=1,
    )

    # When
    step.set_nonce_and_sign_transaction(transaction)

    # Then
    assert transaction.nonce == 1
    assert transaction.signature == b"aaaaa"
