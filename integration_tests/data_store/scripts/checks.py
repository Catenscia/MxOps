from mxops.data.execution_data import ScenarioData
from mxops.data.utils import json_loads


def check_storage(contract_id: str, expected_data_str: str) -> bool:
    """
    Check the content of the storage for a contract. The function verify that the
    provided data is in the saved data of the contract. (no equivalence, just inclusion)

    :param contract_id: id of the contract to check the storeage of
    :type contract_id: str
    :param expected_data_str: dictionary as string representing the expected data
    :type expected_data_str: str
    """
    scenario_data = ScenarioData.get()
    expected_data = json_loads(expected_data_str)
    for key, value in expected_data.items():
        saved_value = scenario_data.get_contract_value(contract_id, key)
        if saved_value != value:
            raise ValueError(
                f"Expected {value} but found {saved_value} for the key {key}"
            )
