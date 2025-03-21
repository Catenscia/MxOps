import pytest
from mxops.data.execution_data import AccountData, ScenarioData
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
