from typing import Any
from mxops.data.execution_data import ScenarioData
from mxops.data.utils import json_loads


def check_storage_elements(storage: Any, expected: Any) -> bool:
    """
    Recursively check if the elements of a storage correspond to the expected elements
    Add some conversion between type not handeled by json like tuples

    :param storage: values found in MxOps storage
    :type storage: Any
    :param expected: expected values
    :type expected: Any
    :return: if the values matches
    :rtype: bool
    """
    if isinstance(storage, dict) and isinstance(expected, dict):
        if len(storage) != len(expected):
            return False
        return all(
            [
                check_storage_elements(*arg)
                for arg in zip(sorted(storage.items()), sorted(expected.items()))
            ]
        )
    if isinstance(storage, (list, set, tuple)):
        if not isinstance(storage, (list, set, tuple)):
            return False
        if len(storage) != len(expected):
            return False
        return all([check_storage_elements(*arg) for arg in zip(storage, expected)])
    return storage == expected


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
        saved_value = scenario_data.get_account_value(contract_id, key)
        if not check_storage_elements(saved_value, value):
            raise ValueError(
                f"Expected {value} but found {saved_value} for the key {key}"
            )
