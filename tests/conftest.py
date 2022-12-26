
import pytest
import yaml

from xops.config.config import Config
from xops.data.data import ContractData, ScenarioData, delete_scenario_data
from xops.enums import NetworkEnum


@pytest.fixture(scope='session', autouse=True)
def network():
    Config.set_network(NetworkEnum.LOCAL)


@pytest.fixture(scope='session', autouse=True)
def scenario_data():
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

@pytest.fixture(scope='function')
def deploy_yaml_content():
    with open('./tests/data/deploy_scene.yaml', encoding='utf-8') as file:
        return yaml.safe_load(file)
