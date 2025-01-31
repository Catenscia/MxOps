from dataclasses import dataclass
import time

from multiversx_sdk import Address, NetworkStatus, Token, TokenTransfer
from unittest.mock import patch

from mxops.data.execution_data import ScenarioData
from mxops.execution.steps.base import Step
from mxops.execution.steps import LoopStep, SetVarsStep, WaitStep
from mxops.execution.smart_values import (
    SmartAddress,
    SmartBech32,
    SmartBool,
    SmartDict,
    SmartInt,
    SmartList,
    SmartStr,
    SmartTokenTransfer,
    SmartTokenTransfers,
    SmartValue,
)
from mxops.execution.steps.factory import SmartStep, SmartSteps


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
    assert step.smart_step.get_evaluated_value() == SetVarsStep(
        variables={"counter": 0}
    )
    assert step.smart_steps.get_evaluated_value() == [
        SetVarsStep(variables={"counter": 0})
    ]


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
    assert step.smart_step.get_evaluated_value() == SetVarsStep(
        variables={"counter": 0}
    )
    assert step.smart_steps.get_evaluated_value() == [
        SetVarsStep(variables={"counter": 0})
    ]


def test_loop_step_with_range():
    # Given
    step = LoopStep(
        [
            {"type": "Loop", "var_name": "loop_var_2", "steps": [], "var_list": []},
            {"type": "SetVars", "variables": {"counter": 0}},
        ],
        "loop_var",
        var_start=0,
        var_end=2,
    )
    scenario_data = ScenarioData.get()

    # When / Then
    for i, step in enumerate(step.generate_steps()):
        assert scenario_data.get_value("loop_var") == i // 2
        if i % 2 == 0:
            assert step == LoopStep(steps=[], var_name="loop_var_2", var_list=[])
        else:
            assert step == SetVarsStep(variables={"counter": 0})
    assert i == 3  # (2 - 0) * 2


def test_loop_step_with_list():
    # Given
    var_list = ["hey", 42]
    step = LoopStep(
        [
            {"type": "Loop", "var_name": "loop_var_2", "steps": [], "var_list": []},
            {"type": "SetVars", "variables": {"counter": 0}},
        ],
        "loop_var",
        var_list=var_list,
    )
    scenario_data = ScenarioData.get()

    # When / Then
    for i, step in enumerate(step.generate_steps()):
        assert scenario_data.get_value("loop_var") == var_list[i // 2]
        if i % 2 == 0:
            assert step == LoopStep(steps=[], var_name="loop_var_2", var_list=[])
        else:
            assert step == SetVarsStep(variables={"counter": 0})
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
