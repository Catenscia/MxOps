import json
from pathlib import Path
from typing import Any, List

import pytest
from mxops import errors

from mxops.data.execution_data import (
    _ScenarioData,
    InternalContractData,
    SavedValuesData,
    TokenData,
    parse_value_key,
)
from mxops.enums import NetworkEnum, TokenTypeEnum


@pytest.mark.parametrize(
    "scenario_path",
    [
        Path("tests/data/scenarios/scenario_A.json"),
        Path("tests/data/scenarios/scenario_B.json"),
    ],
)
def test_scenario_loading(scenario_path: Path):
    """
    Test that contract data is correctly loaded and that both environment syntax are
    handeld
    """
    # Given
    # When
    scenario = _ScenarioData.load_from_path(scenario_path)

    # Then
    assert scenario.network == NetworkEnum.DEV
    assert scenario.name == "___test_mxops_tutorial_first_scene"
    assert scenario.contracts_data == {
        "egld-ping-pong": InternalContractData(
            contract_id="egld-ping-pong",
            address="erd1qqqqqqqqqqqqqpgq0048vv3uk6l6cdreezpallvduy4qnfv2plcq74464k",
            saved_values={},
            wasm_hash=(
                "5ce403a4f73701481cc15b2378cdc5bce3e35fa215815aa5eb9104d9f7ab2451"
            ),
            deploy_time=1677134892,
            last_upgrade_time=1677134892,
        )
    }


def test_key_path_fetch():
    """
    Test that data is fetched correctly from a key path
    """
    # Given
    saved_values = SavedValuesData(
        saved_values={
            "key_1": {
                "key_2": [
                    {"data": "wrong value"},
                    {"data": "wrong value"},
                    {"data": "desired value"},
                ]
            }
        }
    )

    # When
    data = saved_values.get_value("key_1.key_2[2].data")

    # Then
    assert data == "desired value"


def test_key_path_fetch_errors():
    """
    Test that errors are correctly raise for wrong key path
    """
    # Given
    saved_values = SavedValuesData(
        saved_values={
            "key_1": {
                "key_2": [
                    {"data": "wrong value"},
                    {"data": "wrong value"},
                    {"data": "desired value"},
                ]
            }
        }
    )

    # When
    try:
        saved_values.get_value("key_3")
        raise RuntimeError("An error should have been raised by the line above")
    except errors.WrongDataKeyPath as err:
        assert err.args == (
            "Wrong key 'key_3' in ['key_3'] for data element {'key_1': {'key_2': "
            "[{'data': "
            "'wrong value'}, {'data': 'wrong value'}, {'data': 'desired value'}]}}",
        )
    try:
        saved_values.get_value("key_1.key_3")
        raise RuntimeError("An error should have been raised by the line above")
    except errors.WrongDataKeyPath as err:
        assert err.args == (
            "Wrong key 'key_3' in ['key_1', 'key_3'] for data element {'key_2': "
            "[{'data': 'wrong value'}, {'data': 'wrong value'}, {'data': "
            "'desired value'}]}",
        )
    try:
        saved_values.get_value("key_1.key_2[4]")
        raise RuntimeError("An error should have been raised by the line above")
    except errors.WrongDataKeyPath as err:
        assert err.args == (
            "Wrong index 4 in ['key_1', 'key_2', 4] for data element [{'data': "
            "'wrong value'}, {'data': 'wrong value'}, {'data': 'desired value'}]",
        )


@pytest.mark.parametrize(
    "value_key, expected_result",
    [
        ("key_1.key_2[0].data", ["key_1", "key_2", 0, "data"]),
        ("ping_pong.address", ["ping_pong", "address"]),
        ("ping-pong.address", ["ping-pong", "address"]),
    ],
)
def test_parse_value_key(value_key: str, expected_result: List[str | int]):
    # When
    # Given
    result = parse_value_key(value_key)

    # Then
    assert result == expected_result


@pytest.mark.parametrize(
    "key_path, value",
    [
        ("key_1.key_2[0].data", "value"),
        ("key_1[0][0].data", 1584),
        ("key_3", [1, 5, 6, 8]),
    ],
)
def test_key_path_set(key_path: str, value: Any):
    """
    Test that values can be set and retrieved correctly
    """
    # Given
    saved_values = SavedValuesData(saved_values={})

    # When
    saved_values.set_value(key_path, value)
    retrieved_value = saved_values.get_value(key_path)

    # Then
    assert retrieved_value == value


def test_key_path_set_errors():
    """
    Test that errors are correctly raise for wrong key path
    """
    # Given
    saved_values = SavedValuesData(
        saved_values={
            "key_1": {
                "key_2": [
                    {"data": "wrong value"},
                    {"data": "wrong value"},
                    {"data": "desired value"},
                ]
            }
        }
    )

    # When
    try:
        saved_values.set_value("", "value")
        raise RuntimeError("An error should have been raised by the line above")
    except errors.WrongDataKeyPath as err:
        assert err.args == ("Key path is empty",)
    try:
        saved_values.set_value("[1]", "value")
        raise RuntimeError("An error should have been raised by the line above")
    except errors.WrongDataKeyPath as err:
        assert err.args[0].startswith("Expected a tuple or a list but found {")
    try:
        saved_values.set_value("key_1.key_2.key_3", "value")
        raise RuntimeError("An error should have been raised by the line above")
    except errors.WrongDataKeyPath as err:
        assert err.args[0].startswith("Expected a dict but found [")


def test_token_data_loading():
    """
    Test that token data is correctly loaded
    """
    # Given
    scenario_path = Path("tests/data/scenarios/scenario_C.json")

    # When
    scenario = _ScenarioData.load_from_path(scenario_path)

    # Then
    assert scenario.tokens_data == {
        "My Token": TokenData(
            name="My Token",
            ticker="MTK",
            identifier="MTK-abcdef",
            saved_values={},
            type=TokenTypeEnum.FUNGIBLE,
        )
    }


def test_io_unicity():
    """
    Test the loading and writing are consistent
    """
    # Given
    scenario_path = Path("tests/data/scenarios/scenario_C.json")
    with open(scenario_path.as_posix(), encoding="utf-8") as file:
        raw_data = json.load(file)

    # When
    scenario = _ScenarioData.load_from_path(scenario_path)
    scenario_dict = scenario.to_dict()

    # Then
    assert scenario_dict == raw_data
