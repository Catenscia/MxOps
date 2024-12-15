import os
from typing import Any

from multiversx_sdk_cli.contracts import SmartContract
import pytest

from mxops.data.execution_data import _ScenarioData
from mxops.execution import utils


def test_env_value():
    # Given
    var_name = "PYTEST_MXOPS_VALUE"
    var_value = 784525
    os.environ[var_name] = str(var_value)

    # When
    retrieved_value = utils.retrieve_value_from_string(f"${var_name}:int")

    # Then
    assert retrieved_value == var_value


def test_scenario_attribute_data():
    # Given
    contract_id = "my_test_contract"
    address = "erd1qqqqqqqqqqqqqpgqdmq43snzxutandvqefxgj89r6fh528v9dwnswvgq9t"

    # When
    arg = f"%{contract_id}.address"
    retrieved_value = utils.retrieve_value_from_string(arg)

    # Then
    assert retrieved_value == address


def test_scenario_saved_data(scenario_data: _ScenarioData):
    # Given
    contract_id = "my_test_contract"
    scenario_data.set_contract_value(contract_id, "my_key", 7458)

    # When
    arg = f"%{contract_id}.my_key:int"
    retrieved_value = utils.retrieve_value_from_string(arg)

    # Then
    assert retrieved_value == 7458


def test_value_from_config():
    # Given
    expected_value = "localnet"
    value_name = "CHAIN"

    # When
    arg = f"&{value_name}"
    retrieved_value = utils.retrieve_value_from_string(arg)

    # Then
    assert retrieved_value == expected_value


def test_address_from_account():
    # Given
    # When
    retrieved_value = utils.get_address_instance("test_user_A")

    # Then
    assert (
        retrieved_value.to_bech32()
        == "erd1jzw34pun678ktsstunk0dm0z2uh7m0ld9trw507ksnzt0wxalwwsv3fpa2"
    )


def test_get_contract_instance():
    """
    Test that a contract can be retrieved correctly
    """
    # Given
    contract_id = "my_test_contract"

    # When
    contract = utils.get_contract_instance(contract_id)
    contract_bis = utils.get_contract_instance(
        "erd1qqqqqqqqqqqqqpgqdmq43snzxutandvqefxgj89r6fh528v9dwnswvgq9t"
    )

    # Then
    assert isinstance(contract, SmartContract)
    assert isinstance(contract_bis, SmartContract)
    assert contract.address.bech32() == contract_bis.address.bech32()


def test_retrieve_contract_address():
    """
    Test that a contract address can be retrieved
    """
    # Given
    contract_id = "my_test_contract"

    # When
    address = utils.retrieve_value_from_string(f"%{contract_id}.address")

    # Assert
    assert isinstance(address, str)
    address == "erd1qqqqqqqqqqqqqpgqdmq43snzxutandvqefxgj89r6fh528v9dwnswvgq9t"


def test_retrieve_account_address_from_data():
    """
    Test that an account address can be retrieved
    """
    # Given
    account_id = "test_user_A"

    # When
    address = utils.retrieve_value_from_string(f"%{account_id}.address")

    # Assert
    assert isinstance(address, str)
    address == "erd1jzw34pun678ktsstunk0dm0z2uh7m0ld9trw507ksnzt0wxalwwsv3fpa2"


@pytest.mark.parametrize(
    "arg, expected_result",
    [
        ("%user", "alice"),
        (
            "%{%{user}.address}",
            "erd1pqslfwszea4hrxdvluhr0v7dhgdfwv6ma70xef79vruwnl7uwkdsyg4xj3",
        ),
        (
            "%%{user}.address",
            "erd1pqslfwszea4hrxdvluhr0v7dhgdfwv6ma70xef79vruwnl7uwkdsyg4xj3",
        ),
        ("$OWNER_NAME", "bob"),
        ("${OWNER_NAME}", "bob"),
        (
            "%{${OWNER_NAME}.address}",
            "erd1ddhla0htp9eknfjn628ut55qafcpxa9evxmps2aflq8ldgqq08esc3x3f8",
        ),
        (
            ["%%{user}.address", "%{${OWNER_NAME}.address}"],
            [
                "erd1pqslfwszea4hrxdvluhr0v7dhgdfwv6ma70xef79vruwnl7uwkdsyg4xj3",
                "erd1ddhla0htp9eknfjn628ut55qafcpxa9evxmps2aflq8ldgqq08esc3x3f8",
            ],
        ),
        ("%my_list", ["item1", "item2", "item3", {"item4-key1": "e"}]),
        ("%my_list[0]", "item1"),
        ("%{my_list[0]}b", "item1b"),
        ("%{my_list[0]}%{my_list[1]}%{my_list[3].item4-key1}", "item1item2e"),
        ("%my_dict", {"key1": "1", "key2": 2, "key3": ["x", "y", "z"]}),
        ("%my_dict.key1", "1"),
        ("%my_dict.key1:int", 1),
        ("%my_dict.key2", 2),
        ("%{my_dict.key2}_", "2_"),
        ("%{${OWNER_NAME}_%{suffix}.identifier}", "BOBT-123456"),
    ],
)
def test_string_retrieval(arg: Any, expected_result: Any):
    # Given
    # When
    retrieved_value = utils.retrieve_value_from_any(arg)

    # Then
    assert retrieved_value == expected_result
