from dataclasses import dataclass
from mxops.execution.steps.base import Step
from mxops.execution.smart_values import (
    SmartAddress,
    SmartBech32,
    SmartBool,
    SmartInt,
    SmartStr,
    SmartTokenTransfer,
    SmartTokenTransfers,
    SmartValue,
)


@dataclass
class TestStep(Step):
    smart_value: SmartValue
    smart_int: SmartInt
    smart_bool: SmartBool
    smart_str: SmartStr
    smart_address: SmartAddress
    smart_bech32: SmartBech32
    smart_token_transfer: SmartTokenTransfer
    smart_token_transfers: SmartTokenTransfers

    def execute(self):
        pass


def test_smart_values_auto_conversion():
    """
    Check that the values are converted into the correct smart values
    """
    # Given
    step = TestStep(
        1,
        1,
        "True",
        "hello",
        "erd1qqqqqqqqqqqqqpgq0048vv3uk6l6cdreezpallvduy4qnfv2plcq74464k",
        "erd1qqqqqqqqqqqqqpgq0048vv3uk6l6cdreezpallvduy4qnfv2plcq74464k",
        ["WEGLD-abcdef", 123456],
        [["WEGLD-abcdef", 123456]],
    )

    # When
    # Then
    assert isinstance(step.smart_value, SmartValue)
    assert isinstance(step.smart_int, SmartInt)
    assert isinstance(step.smart_bool, SmartBool)
    assert isinstance(step.smart_str, SmartStr)
    assert isinstance(step.smart_address, SmartAddress)
    assert isinstance(step.smart_bech32, SmartBech32)
    assert isinstance(step.smart_token_transfer, SmartTokenTransfer)
    assert isinstance(step.smart_token_transfers, SmartTokenTransfers)


def test_smart_values_normal_instantiation():
    """
    Check that nothing is changed when supplied values already have the correct type
    """
    # Given
    step = TestStep(
        SmartValue(1),
        SmartInt(1),
        SmartBool("True"),
        SmartStr("hello"),
        SmartAddress("erd1qqqqqqqqqqqqqpgq0048vv3uk6l6cdreezpallvduy4qnfv2plcq74464k"),
        SmartBech32("erd1qqqqqqqqqqqqqpgq0048vv3uk6l6cdreezpallvduy4qnfv2plcq74464k"),
        SmartTokenTransfer(["WEGLD-abcdef", 123456]),
        SmartTokenTransfers([["WEGLD-abcdef", 123456]]),
    )

    # When
    # Then
    assert step.smart_value == SmartValue(1)
    assert step.smart_int == SmartInt(1)
    assert step.smart_bool == SmartBool("True")
    assert step.smart_str == SmartStr("hello")
    assert step.smart_address == SmartAddress(
        "erd1qqqqqqqqqqqqqpgq0048vv3uk6l6cdreezpallvduy4qnfv2plcq74464k"
    )
    assert step.smart_bech32 == SmartBech32(
        "erd1qqqqqqqqqqqqqpgq0048vv3uk6l6cdreezpallvduy4qnfv2plcq74464k"
    )
    assert step.smart_token_transfer == SmartTokenTransfer(["WEGLD-abcdef", 123456])
    assert step.smart_token_transfers == SmartTokenTransfers([["WEGLD-abcdef", 123456]])
