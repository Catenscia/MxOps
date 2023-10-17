"""
Custom module from a user
"""
from typing import Any
from mxops.data.execution_data import ScenarioData


def set_contract_value(contract_id: str, value_key: str, value: Any):
    """
    Set a key, value pair for a contract

    :param contract_id: contract to set the value of
    :type contract_id: str
    :param value_key: key under which save the value
    :type value_key: str
    :param value: value to save
    :type value: Any
    """
    scenario_data = ScenarioData.get()
    scenario_data.set_contract_value(contract_id, value_key, value)
    return str(value)
