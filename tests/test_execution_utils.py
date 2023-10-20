import os

from multiversx_sdk_cli.accounts import Account
from multiversx_sdk_cli.contracts import SmartContract
from multiversx_sdk_core import Address

from mxops.data.execution_data import _ScenarioData
from mxops.execution import utils
from mxops.execution.account import AccountsManager


def test_no_type():
    # Given
    arg = "MyTokenIdentifier"

    # When
    retrieved_arg, specified_type = utils.retrieve_specified_type(arg)

    # Then
    assert retrieved_arg == arg
    assert specified_type is None


def test_int_type():
    # Given
    arg = "MyTokenAmount:int"

    # When
    retrieved_arg, specified_type = utils.retrieve_specified_type(arg)

    # Then
    assert retrieved_arg == "MyTokenAmount"
    assert specified_type == "int"


def test_env_value():
    # Given
    var_name = "PYTEST_MXOPS_VALUE"
    var_value = 784525
    os.environ[var_name] = str(var_value)

    # When
    retrieved_value = utils.retrieve_value_from_env(f"${var_name}:int")

    # Then
    assert retrieved_value == var_value


def test_scenario_attribute_data():
    # Given
    contract_id = "my_test_contract"
    address = "erd1qqqqqqqqqqqqqpgqdmq43snzxutandvqefxgj89r6fh528v9dwnswvgq9t"

    # When
    arg = f"%{contract_id}.address"
    retrieved_value = utils.retrieve_value_from_scenario_data(arg)

    # Then
    assert retrieved_value == address


def test_scenario_saved_data(scenario_data: _ScenarioData):
    # Given
    contract_id = "my_test_contract"
    scenario_data.set_contract_value(contract_id, "my_key", 7458)

    # When
    arg = f"%{contract_id}.my_key:int"
    retrieved_value = utils.retrieve_value_from_scenario_data(arg)

    # Then
    assert retrieved_value == 7458


def test_value_from_config():
    # Given
    expected_value = "local-testnet"
    value_name = "CHAIN"

    # When
    arg = f"&{value_name}"
    retrieved_value = utils.retrieve_value_from_config(arg)

    # Then
    assert retrieved_value == expected_value


def test_address_from_account():
    # Given
    address = Address.from_bech32(
        "erd1qyu5wthldzr8wx5c9ucg8kjagg0jfs53s8nr3zpz3hypefsdd8ssycr6th"
    )
    account_name = "alice"
    account = Account(address)
    AccountsManager._accounts[account_name] = account

    # When
    arg = f"[{account_name}]"
    retrieved_value = utils.retrieve_address_from_account(arg)

    # Then
    assert retrieved_value == address


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
