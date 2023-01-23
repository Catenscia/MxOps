from pathlib import Path
import pytest
import yaml

from mxops.config.config import Config
from mxops.data.data import ContractData, ScenarioData, delete_scenario_data
from mxops.data.path import initialize_data_folder
from mxops.enums import NetworkEnum


@pytest.fixture(scope='session', autouse=True)
def network():
    Config.set_network(NetworkEnum.LOCAL)


@pytest.fixture(scope='session', autouse=True)
def test_data_folder_path():
    return Path('./tests/data')


@pytest.fixture(scope='session', autouse=True)
def scenario_data():
    initialize_data_folder()
    ScenarioData.create_scenario('pytest_scenario')
    contract_id = 'my_test_contract'
    address = 'erd1...f217'

    _scenario_data = ScenarioData.get()
    _scenario_data.add_contract_data(ContractData(contract_id,
                                                  address,
                                                  '0x..hash',
                                                  1,
                                                  1,
                                                  {},
                                                  ))

    yield _scenario_data
    delete_scenario_data('pytest_scenario', False)


