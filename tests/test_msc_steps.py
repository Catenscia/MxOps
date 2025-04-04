from dataclasses import dataclass, field
from io import StringIO
from pathlib import Path
import re
import time
from typing import Any

from multiversx_sdk import Address, NetworkStatus, Token, TokenTransfer
from unittest.mock import patch

import pytest

from mxops import errors
from mxops.data.execution_data import ScenarioData
from mxops.execution.scene import execute_step
from mxops.execution.steps.base import Step
from mxops.execution.steps import LoopStep, PythonStep, SetVarsStep, WaitStep
from mxops.smart_values import (
    SmartAddress,
    SmartBech32,
    SmartBool,
    SmartDict,
    SmartInt,
    SmartList,
    SmartPath,
    SmartStr,
    SmartTokenTransfer,
    SmartTokenTransfers,
    SmartValue,
)
from mxops.execution.steps.factory import SmartStep, SmartSteps
from mxops.execution.steps.msc import AssertStep, LogStep, SceneStep, SetSeedStep


@dataclass
class DummyStep(Step):
    smart_value: SmartValue
    smart_int: SmartInt
    smart_bool: SmartBool
    smart_str: SmartStr
    smart_address: SmartAddress
    smart_bech32: SmartBech32
    smart_token_transfer: SmartTokenTransfer
    smart_token_transfers: SmartTokenTransfers
    smart_list: SmartList
    smart_dict: SmartDict
    smart_step: SmartStep
    smart_steps: SmartSteps

    def _execute(self):
        pass


@dataclass
class DummyUnionStep(Step):
    smart_value: SmartValue = field(default_factory=lambda: SmartValue(""))
    smart_int: SmartInt | None = 0
    smart_path: SmartPath | None = None

    def _execute(self):
        pass


def test_step_smart_values_auto_conversion():
    """
    Check that the values are converted into the correct smart values
    """
    # Given
    step = DummyStep(
        1,
        1,
        "True",
        "hello",
        "erd1qqqqqqqqqqqqqpgq0048vv3uk6l6cdreezpallvduy4qnfv2plcq74464k",
        "erd1qqqqqqqqqqqqqpgq0048vv3uk6l6cdreezpallvduy4qnfv2plcq74464k",
        ["WEGLD-abcdef", 123456],
        [["WEGLD-abcdef", 123456]],
        [],
        {},
        {"type": "SetVars", "variables": {"counter": 0}},
        [{"type": "SetVars", "variables": {"counter": 0}}],
    )

    # When
    step.evaluate_smart_values()

    # Then
    assert step.smart_value.get_evaluated_value() == 1
    assert step.smart_int.get_evaluated_value() == 1
    assert step.smart_bool.get_evaluated_value() is True
    assert step.smart_str.get_evaluated_value() == "hello"
    assert step.smart_address.get_evaluated_value() == Address.new_from_bech32(
        "erd1qqqqqqqqqqqqqpgq0048vv3uk6l6cdreezpallvduy4qnfv2plcq74464k"
    )
    assert step.smart_bech32.get_evaluated_value() == (
        "erd1qqqqqqqqqqqqqpgq0048vv3uk6l6cdreezpallvduy4qnfv2plcq74464k"
    )
    assert step.smart_token_transfer.get_evaluated_value() == TokenTransfer(
        Token("WEGLD-abcdef"), 123456
    )
    assert step.smart_token_transfers.get_evaluated_value() == [
        TokenTransfer(Token("WEGLD-abcdef"), 123456)
    ]
    assert step.smart_list.get_evaluated_value() == []
    assert step.smart_dict.get_evaluated_value() == {}
    expected_set_vars_step = SetVarsStep(variables={"counter": 0})
    assert step.smart_step.get_evaluated_value() == expected_set_vars_step
    assert step.smart_steps.get_evaluated_value() == [expected_set_vars_step]


def test_step_smart_values_normal_instantiation():
    """
    Check that nothing is changed when supplied values already have the correct type
    """
    # Given
    step = DummyStep(
        SmartValue(1),
        SmartInt(1),
        SmartBool("True"),
        SmartStr("hello"),
        SmartAddress("erd1qqqqqqqqqqqqqpgq0048vv3uk6l6cdreezpallvduy4qnfv2plcq74464k"),
        SmartBech32("erd1qqqqqqqqqqqqqpgq0048vv3uk6l6cdreezpallvduy4qnfv2plcq74464k"),
        SmartTokenTransfer(["WEGLD-abcdef", 123456]),
        SmartTokenTransfers([["WEGLD-abcdef", 123456]]),
        SmartList([]),
        SmartDict({}),
        SmartStep({"type": "SetVars", "variables": {"counter": 0}}),
        SmartSteps([{"type": "SetVars", "variables": {"counter": 0}}]),
    )

    # When
    step.evaluate_smart_values()

    # Then
    assert step.smart_value.get_evaluated_value() == 1
    assert step.smart_int.get_evaluated_value() == 1
    assert step.smart_bool.get_evaluated_value() is True
    assert step.smart_str.get_evaluated_value() == "hello"
    assert step.smart_address.get_evaluated_value() == Address.new_from_bech32(
        "erd1qqqqqqqqqqqqqpgq0048vv3uk6l6cdreezpallvduy4qnfv2plcq74464k"
    )
    assert step.smart_bech32.get_evaluated_value() == (
        "erd1qqqqqqqqqqqqqpgq0048vv3uk6l6cdreezpallvduy4qnfv2plcq74464k"
    )
    assert step.smart_token_transfer.get_evaluated_value() == TokenTransfer(
        Token("WEGLD-abcdef"), 123456
    )
    assert step.smart_token_transfers.get_evaluated_value() == [
        TokenTransfer(Token("WEGLD-abcdef"), 123456)
    ]
    assert step.smart_list.get_evaluated_value() == []
    assert step.smart_dict.get_evaluated_value() == {}
    expected_set_vars_step = SetVarsStep(variables={"counter": 0})
    assert step.smart_step.get_evaluated_value() == expected_set_vars_step
    assert step.smart_steps.get_evaluated_value() == [expected_set_vars_step]


def test_smart_values_with_default_instantiation_1():
    # Given
    step = DummyUnionStep()

    # When
    step.evaluate_smart_values()

    # Then
    assert step.smart_value.get_evaluated_value() == ""
    assert step.smart_int.get_evaluated_value() == 0
    assert step.smart_path is None


def test_smart_values_with_default_instantiation_2():
    # Given
    step = DummyUnionStep("test", 123456, "./my/path/to/folder")

    # When
    step.evaluate_smart_values()

    # Then
    assert step.smart_value.get_evaluated_value() == "test"
    assert step.smart_int.get_evaluated_value() == 123456
    assert step.smart_path.get_evaluated_value() == Path("./my/path/to/folder")


def test_loop_step_with_range():
    # Given
    step = LoopStep(
        [
            {"type": "Loop", "var_name": "loop_var_2", "steps": [], "var_list": [1, 2]},
            {"type": "SetVars", "variables": {"counter": 0}},
        ],
        "loop_var",
        var_start=0,
        var_end=2,
    )
    scenario_data = ScenarioData.get()

    # When / Then
    expected_loop_step = LoopStep(steps=[], var_name="loop_var_2", var_list=[1, 2])
    expected_set_vars_step = SetVarsStep(variables={"counter": 0})

    for i, step in enumerate(step.generate_steps()):
        assert scenario_data.get_value("loop_var") == i // 2
        if i % 2 == 0:
            assert step == expected_loop_step
        else:
            assert step == expected_set_vars_step
    assert i == 3  # (2 - 0) * 2


def test_loop_step_with_list():
    # Given
    var_list = ["hey", 42]
    step = LoopStep(
        [
            {"type": "Loop", "var_name": "loop_var_2", "steps": [], "var_list": [1, 2]},
            {"type": "SetVars", "variables": {"counter": 0}},
        ],
        "loop_var",
        var_list=var_list,
    )
    scenario_data = ScenarioData.get()

    # When / Then
    expected_loop_step = LoopStep(steps=[], var_name="loop_var_2", var_list=[1, 2])
    expected_set_vars_step = SetVarsStep(variables={"counter": 0})

    for i, step in enumerate(step.generate_steps()):
        assert scenario_data.get_value("loop_var") == var_list[i // 2]
        if i % 2 == 0:
            assert step == expected_loop_step
        else:
            assert step == expected_set_vars_step
    assert i == 3  # (2 - 0) * 2


def test_set_vars_step():
    # Given
    scenario_data = ScenarioData.get()
    step = SetVarsStep(
        variables={
            "test_set_vars_step_var1": "%{${OWNER_NAME}_%{suffix}.identifier}",
            "test_set_vars_step_var2": "%my_dict",
        }
    )

    # When
    step.execute()

    # Then
    assert scenario_data.get_value("test_set_vars_step_var1") == "BOBT-123456"
    assert scenario_data.get_value("test_set_vars_step_var2") == {
        "key1": "1",
        "key2": 2,
        "key3": ["x", "y", "z"],
    }


def test_time_wait_step():
    # Given
    step = WaitStep(for_seconds=0.1)

    # When
    t0 = time.time()
    step.execute()

    # Then
    assert 0.11 > time.time() - t0 > 0.1


def test_block_wait_step():
    # Given
    step = WaitStep(for_blocks=1)
    side_effect = [
        NetworkStatus({}, 0, 10, 10, 1, 1),
        NetworkStatus({}, 0, 10, 10, 1, 1),
        NetworkStatus({}, 0, 11, 10, 1, 1),
    ]

    # When
    with patch(
        "mxops.config.config.ProxyNetworkProvider.get_network_status"
    ) as mock_method:
        mock_method.side_effect = side_effect
        t0 = time.time()
        step.execute()

    # Then
    assert 3 * 0.2 > time.time() - t0 > 2 * 0.2  # wait time between network status call


def test_python_step():
    # Given
    scenario_data = ScenarioData.get()
    module_path = "./tests/data/custom_user_module.py"
    function = "set_contract_value"
    step_1 = PythonStep(
        module_path,
        function,
        ["my_test_contract", "my_test_key", "my_test_value"],
        log_result=True,
        result_save_key="result_1",
    )

    step_2 = PythonStep(
        module_path,
        function,
        keyword_arguments={
            "contract_id": "my_test_contract",
            "value_key": "my_test_key",
            "value": 4582,
        },
        log_result=True,
        result_save_key="result_2",
    )

    # When
    step_1.execute()
    value_1 = scenario_data.get_account_value("my_test_contract", "my_test_key")
    scenario_value_1 = scenario_data.get_value("result_1")
    step_2.execute()
    value_2 = scenario_data.get_account_value("my_test_contract", "my_test_key")
    scenario_value_2 = scenario_data.get_value("result_2")

    # Then
    assert value_1 == "my_test_value"
    assert scenario_value_1 == "my_test_value"
    assert value_2 == 4582
    assert scenario_value_2 == 4582


def test_direct_set_vars_step():
    # Given
    scenario_data = ScenarioData.get()
    variables = {
        "int-var": 1,
        "str-var": "hello",
        "list-var": [1, 2, "a", [1, 3]],
        "dict-var": {"a": 23, 23: ["a", 124]},
    }
    step = SetVarsStep(variables)

    # When
    step.execute()

    # Then
    saved_values = {key: scenario_data.get_value(key) for key in variables}
    assert variables == saved_values


def test_reference_set_vars_step():
    # Given
    scenario_data = ScenarioData.get()
    scenario_data.set_value("reg-list", [1, 2, 3])
    scenario_data.set_value("reg-name", "bob")
    scenario_data.set_value("reg-value", 1)
    variables = {
        "int-var": "%reg-value",
        "str-var": "%reg-name",
        "list-var": [1, 2, "a", "%reg-list"],
        "dict-var": {"%reg-name": 23, 23: ["%reg-name", "%reg-list"]},
    }
    step = SetVarsStep(variables)

    # When
    step.execute()

    # Then
    expected_result = {
        "int-var": 1,
        "str-var": "bob",
        "list-var": [1, 2, "a", [1, 2, 3]],
        "dict-var": {"bob": 23, 23: ["bob", [1, 2, 3]]},
    }
    saved_values = {key: scenario_data.get_value(key) for key in variables}
    assert expected_result == saved_values


def register_value_in_list(value: Any):
    scenario_data = ScenarioData.get()
    try:
        register_list = scenario_data.get_value("register_list")
    except errors.WrongDataKeyPath:
        register_list = []
    register_list.append(value)
    scenario_data.set_value("register_list", register_list)


def test_loop_step_from_scenario_data_list():
    # Given
    scenario_data = ScenarioData.get()
    scenario_data.set_value("var_list", [1, 2, 4])
    loop_step = LoopStep(
        steps=[
            PythonStep(
                "./tests/test_msc_steps.py", "register_value_in_list", ["%loop_var"]
            )
        ],
        var_name="loop_var",
        var_list="%var_list",
    )

    # When
    for step in loop_step.generate_steps():
        step.execute()

    # Then
    assert scenario_data.get_value("register_list") == [1, 2, 4]


def test_scene_repeat_step():
    # Given
    scenario_data = ScenarioData.get()
    scenario_data.set_value("scene_counter", 0)
    step = SceneStep(path=Path("tests/data/scenes/increment_scene.yaml"), repeat=10)

    # When
    execute_step(step, scenario_data)

    # Then
    assert scenario_data.get_value("scene_counter") == 10


def test_scene_folder_repeat_step():
    # Given
    scenario_data = ScenarioData.get()
    scenario_data.set_value("scene_counter", 0)
    step = SceneStep(
        path=Path("tests/data/scenes/multiple_scenes_increment"), repeat=10
    )

    # When
    execute_step(step, scenario_data)

    # Then
    assert scenario_data.get_value("scene_counter") == 20


def test_nested_loop_composition():
    # Given
    scenario_data = ScenarioData.get()
    step = SceneStep(
        path=Path("tests/data/scenes/nested_loop_composition.yaml"), repeat=10
    )

    # When
    execute_step(step, scenario_data)

    # Then
    for counter_1 in range(0, 10):
        for counter_2 in range(0, 10):
            assert (
                scenario_data.get_value(f"pair_{counter_1}_{counter_2}")
                == counter_1 * counter_2
            )


def test_loop_dependant_set_vars():
    # Given
    step = LoopStep(
        [
            {"type": "SetVars", "variables": {"myvar123456": "heyheyhey%{loop_var}"}},
            {"type": "SetVars", "variables": {"%{myvar123456}": 156}},
        ],
        "loop_var",
        var_start=0,
        var_end=2,
    )
    scenario_data = ScenarioData.get()

    # When
    for step in step.generate_steps():
        step.execute()

    # Then
    assert scenario_data.get_value("myvar123456") == "heyheyhey1"
    assert scenario_data.get_value("heyheyhey0") == 156
    assert scenario_data.get_value("heyheyhey1") == 156


def test_set_vars_sequentially_dependent_variables():
    # Given
    step = SetVarsStep({"a": 10, "b": "={%{a} + 2}"})
    scenario_data = ScenarioData.get()

    # When
    step.execute()

    # Then
    assert scenario_data.get_value("%a") == 10
    assert scenario_data.get_value("%b") == 12


def test_set_seed_randomness():
    # Given
    value_a = SmartValue("=randint(0,10**18)")
    value_b = SmartValue("=randint(0,10**18)")
    value_c = SmartValue("=randint(0,10**18)")
    step = SetSeedStep(42)

    # When
    step.execute()
    value_a.evaluate()
    value_b.evaluate()
    step.execute()
    value_c.evaluate()

    # Then
    assert value_a.get_evaluated_value() != value_b.get_evaluated_value()
    assert value_a.get_evaluated_value() == value_c.get_evaluated_value()


def test_true_assertions():
    # Given
    step = AssertStep(
        [
            True,
            1,
            "={1 > 0}",
            "={'%{alice.address}' == 'erd1pqslfwszea4hrxdvluhr0v7dhgdfwv6ma70xef79vruwnl7uwkdsyg4xj3'}",  # noqa
            "={'item1' in %{my_list}}",
        ]
    )
    # When / Then
    step.execute()


@pytest.mark.parametrize(
    "expression, expected_error_message",
    [
        (False, "False"),
        (
            "={'%{alice.address}' != 'erd1pqslfwszea4hrxdvluhr0v7dhgdfwv6ma70xef79vruwnl7uwkdsyg4xj3'}",  # noqa
            "(={'%{alice.address}' != 'erd1pqslfwszea4hrxdvluhr0v7dhgdfwv6ma70xef79vruwnl7uwkdsyg4xj3'} -> ={'erd1pqslfwszea4hrxdvluhr0v7dhgdfwv6ma70xef79vruwnl7uwkdsyg4xj3' != 'erd1pqslfwszea4hrxdvluhr0v7dhgdfwv6ma70xef79vruwnl7uwkdsyg4xj3'})",  # noqa
        ),
        (
            "={'item1' not in %{my_list}}",
            "(={'item1' not in %{my_list}} -> ={'item1' not in ['item1', 'item2', 'item3', {'item4-key1': 'e'}]})",  # noqa
        ),
    ],
)
def test_false_assertion(expression: Any, expected_error_message: str):
    # Given
    step = AssertStep([expression])

    # When / Then
    with pytest.raises(errors.AssertionFailed, match=re.escape(expected_error_message)):
        step.execute()


def test_log_step(exec_log_capture: StringIO):
    # Given
    step = LogStep(
        error="Error message %{my_list}",
        warning="Warning message %{alice.address}",
        info="Info message ={1+1}",
        debug="Debug message ={'%{my_list[0]}' + '%{my_list[1]}'}",
    )

    # When
    step.execute()

    # Assert
    log_outputs = exec_log_capture.getvalue().splitlines()
    assert log_outputs == [
        "ERROR: Error message ['item1', 'item2', 'item3', {'item4-key1': 'e'}]",
        "WARNING: Warning message erd1pqslfwszea4hrxdvluhr0v7dhgdfwv6ma70xef79vruwnl7uwkdsyg4xj3",  # noqa
        "INFO: Info message 2",
        "DEBUG: Debug message item1item2",
    ]
