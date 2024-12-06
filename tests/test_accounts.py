from mxops.data.execution_data import ScenarioData
from mxops.execution.account import AccountsManager


def test_loaded_accounts():
    # Given
    # When
    accounts_manager = AccountsManager()

    # Then
    assert set(accounts_manager._accounts.keys()) == {
        "test_user_A",
        "test_user_B",
        "alice",
        "bob",
        "charlie",
    }
    scenario_data = ScenarioData.get()
    assert scenario_data.get_value("wallets_folder") == ["alice", "bob", "charlie"]
