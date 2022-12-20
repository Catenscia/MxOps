import os
from xops.data.data import _ScenarioData
from xops.execution import utils


def test_no_type():
    # Given
    arg = 'MyTokenIdentifier'

    # When
    retrieved_arg, specified_type = utils.retrieve_specified_type(arg)

    # Then
    assert retrieved_arg == arg
    assert specified_type is None


def test_no_type():
    # Given
    arg = 'MyTokenAmount:int'

    # When
    retrieved_arg, specified_type = utils.retrieve_specified_type(arg)

    # Then
    assert retrieved_arg == 'MyTokenAmount'
    assert specified_type == 'int'


def test_env_value():
    # Given
    var_name = 'PYTEST_XOPS_VALUE'
    var_value = 784525
    os.environ[var_name] = str(var_value)

    # When
    retrieved_value = utils.retrieve_value_from_env(f'${var_name}:int')

    # Then
    assert retrieved_value == var_value


def test_scenario_attribute_data():
    # Given
    contract_id = 'my_test_contract'
    address = 'erd1...f217'

    # When
    arg = f'%{contract_id}%address'
    retrieved_value = utils.retrieve_value_from_scenario_data(arg)

    # Then
    assert retrieved_value == address


def test_scenario_saved_data(scenario_data: _ScenarioData):
    # Given
    contract_id = 'my_test_contract'
    scenario_data.set_contract_value(contract_id, 'my_key', 7458)

    # When
    arg = f'%{contract_id}%my_key:int'
    retrieved_value = utils.retrieve_value_from_scenario_data(arg)

    # Then
    assert retrieved_value == 7458


def test_value_from_config():
    # Given
    expected_value = 'local-testnet'
    value_name = 'CHAIN'

    # When
    arg = f'&{value_name}'
    retrieved_value = utils.retrieve_value_from_config(arg)

    # Then
    assert retrieved_value == expected_value
