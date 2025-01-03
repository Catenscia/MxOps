from typing import Any
import pytest
from mxops import errors
from mxops.data.execution_data import ScenarioData
from mxops.execution.smart_values import SmartBech32, SmartInt, SmartValue


@pytest.mark.parametrize(
    "raw_value, expected_result, expected_str",
    [
        ("abcdef", "abcdef", "abcdef"),
        (
            12241412,
            12241412,
            "12241412",
        ),
        (
            "%{${OWNER_NAME}_%{suffix}.identifier}",
            "BOBT-123456",
            (
                "BOBT-123456 (%{${OWNER_NAME}_%{suffix}.identifier} -> "
                "%{${OWNER_NAME}_token.identifier} -> %{bob_token.identifier})"
            ),
        ),
    ],
)
def test_smart_value(raw_value: Any, expected_result: Any, expected_str: str):
    # Given
    smart_value = SmartValue(raw_value)

    # When
    smart_value.evaluate()

    # Then
    assert smart_value.is_evaluated
    assert smart_value.get_evaluated_value() == expected_result
    assert smart_value.get_evaluation_string() == expected_str


def test_deeply_nested_smart_value():
    # Given
    scenario_data = ScenarioData.get()
    scenario_data.set_value(
        "deep_nested_list",
        ["%my_list", ["%my_dict", "%my_test_contract.query_result_1"]],
    )
    scenario_data.set_value("list_name", "deep_nested_list")
    smart_value = SmartValue("%%list_name")

    # When
    smart_value.evaluate()

    # Then
    assert smart_value.is_evaluated
    assert smart_value.get_evaluated_value() == [
        ["item1", "item2", "item3", {"item4-key1": "e"}],
        [{"key1": "1", "key2": 2, "key3": ["x", "y", "z"]}, [0, 1, {2: "abc"}]],
    ]
    assert smart_value.get_evaluation_string() == (
        "["
        "['item1', 'item2', 'item3', {'item4-key1': 'e'}], "
        "[{'key1': '1', 'key2': 2, 'key3': ['x', 'y', 'z']}, "
        "[0, 1, {2: 'abc'}]]] "
        "(%%list_name -> %deep_nested_list -> "
        "['%my_list', ['%my_dict', '%my_test_contract.query_result_1']])"
    )


def test_infinite_evaluation():
    # Given
    scenario_data = ScenarioData.get()
    scenario_data.set_value("inf_a", "%inf_b")
    scenario_data.set_value("inf_b", "%inf_a")
    smart_value = SmartValue("%inf_a")

    # When
    with pytest.raises(errors.MaxIterationError):
        smart_value.evaluate()


@pytest.mark.parametrize(
    "raw_value, expected_result, expected_str",
    [
        (
            12241412,
            12241412,
            "12241412",
        ),
        (
            "12241412",
            12241412,
            "12241412",
        ),
        (
            3.1415,
            3,
            "3 (3.1415)",
        ),
    ],
)
def test_smart_int(raw_value: Any, expected_result: Any, expected_str: str):
    # Given
    smart_value = SmartInt(raw_value)

    # When
    smart_value.evaluate()

    # Then
    assert smart_value.is_evaluated
    assert smart_value.get_evaluated_value() == expected_result
    assert smart_value.get_evaluation_string() == expected_str


@pytest.mark.parametrize(
    "raw_value, expected_result, expected_str",
    [
        (
            "my_test_contract",
            "erd1qqqqqqqqqqqqqpgqdmq43snzxutandvqefxgj89r6fh528v9dwnswvgq9t",
            (
                "erd1qqqqqqqqqqqqqpgqdmq43snzxutandvqefxgj89r6fh528v9dwnswvgq9t "
                "(my_test_contract)"
            ),
        ),
        (
            "erd1qqqqqqqqqqqqqpgqdmq43snzxutandvqefxgj89r6fh528v9dwnswvgq9t",
            "erd1qqqqqqqqqqqqqpgqdmq43snzxutandvqefxgj89r6fh528v9dwnswvgq9t",
            "erd1qqqqqqqqqqqqqpgqdmq43snzxutandvqefxgj89r6fh528v9dwnswvgq9t",
        ),
        (
            "%user",
            "erd1pqslfwszea4hrxdvluhr0v7dhgdfwv6ma70xef79vruwnl7uwkdsyg4xj3",
            (
                "erd1pqslfwszea4hrxdvluhr0v7dhgdfwv6ma70xef79vruwnl7uwkdsyg4xj3 "
                "(%user -> alice)"
            ),
        ),
    ],
)
def test_smart_bech32(raw_value: Any, expected_result: Any, expected_str: str):
    # Given
    smart_value = SmartBech32(raw_value)

    # When
    smart_value.evaluate()

    # Then
    assert smart_value.is_evaluated
    assert smart_value.get_evaluated_value() == expected_result
    assert smart_value.get_evaluation_string() == expected_str
