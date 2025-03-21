from copy import deepcopy
import pytest
from mxops.data.execution_data import (
    AccountData,
    ContractData,
    ExternalContractData,
    InternalContractData,
    LedgerAccountData,
    PemAccountData,
    SavedValuesData,
    ScenarioData,
    parse_raw_saved_values_data_data,
)
from mxops.errors import AccoundIdAlreadyhasBech32, AccountAlreadyHasId


def test_account_reloading():
    # Given
    scenario_data = ScenarioData.get()
    account_data = AccountData(
        "my_account", "erd1jur80jffvsc59en9398xg0qes2wx9kjugp45xe7xt9gycml3555qxy8ne2"
    )
    account_data_changed_id = AccountData(
        "my_account_2", "erd1jur80jffvsc59en9398xg0qes2wx9kjugp45xe7xt9gycml3555qxy8ne2"
    )
    account_data_changed_address = AccountData(
        "my_account", "erd15kmfa2qnxy3mm560s2kx8u3f7lwyqud82cqpn8xjuau7g9gm89fsxm4lak"
    )

    # When
    scenario_data.add_account_data(account_data)
    scenario_data.add_account_data(account_data)
    with pytest.raises(AccountAlreadyHasId):
        scenario_data.add_account_data(account_data_changed_id)
    with pytest.raises(AccoundIdAlreadyhasBech32):
        scenario_data.add_account_data(account_data_changed_address)


def test_data_equalities():
    # Given
    accounts_data = [
        SavedValuesData(),
        AccountData(
            "account_id",
            "erd1jur80jffvsc59en9398xg0qes2wx9kjugp45xe7xt9gycml3555qxy8ne2",
        ),
        PemAccountData(
            "account_id",
            "erd1jur80jffvsc59en9398xg0qes2wx9kjugp45xe7xt9gycml3555qxy8ne2",
            "path/to.pem",
        ),
        LedgerAccountData(
            "account_id",
            "erd1jur80jffvsc59en9398xg0qes2wx9kjugp45xe7xt9gycml3555qxy8ne2",
            10,
        ),
        ContractData(
            "account_id",
            "erd1jur80jffvsc59en9398xg0qes2wx9kjugp45xe7xt9gycml3555qxy8ne2",
        ),
        InternalContractData(
            "account_id",
            "erd1jur80jffvsc59en9398xg0qes2wx9kjugp45xe7xt9gycml3555qxy8ne2",
            "",
            0,
            0,
        ),
        ExternalContractData(
            "account_id",
            "erd1jur80jffvsc59en9398xg0qes2wx9kjugp45xe7xt9gycml3555qxy8ne2",
        ),
    ]
    # When
    for i, account_i in enumerate(accounts_data):
        for j in range(i, len(accounts_data)):
            account_j = deepcopy(accounts_data[j])
            if i == j:
                assert account_i == account_j
            else:
                assert account_i != account_j


def test_contract_data_from_dict():
    # Given
    raw_data = {
        "__class__": "ExternalContractData",
        "contract_id": "my_contract",
        "bech32": "erd1qqqqqqqqqqqqqpgqdmq43snzxutandvqefxgj89r6fh528v9dwnswvgq9t",
    }

    # When
    contract_data = parse_raw_saved_values_data_data(raw_data)

    # Then
    assert type(contract_data) is ExternalContractData
    assert contract_data.account_id == raw_data["contract_id"]
    assert contract_data.bech32 == raw_data["bech32"]
