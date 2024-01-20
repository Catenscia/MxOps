from pathlib import Path
import pytest

from mxpyserializer.abi_serializer import AbiSerializer

from mxops.config.config import Config
from mxops.data.execution_data import (
    InternalContractData,
    ScenarioData,
    delete_scenario_data,
)
from mxops.data.path import initialize_data_folder
from mxops.enums import NetworkEnum


@pytest.fixture(scope="session", autouse=True)
def network():
    Config.set_network(NetworkEnum.LOCAL)


@pytest.fixture(scope="session", autouse=True)
def test_data_folder_path():
    return Path("./tests/data")


@pytest.fixture(scope="session", autouse=True)
def scenario_data():
    initialize_data_folder()
    ScenarioData.create_scenario("pytest_scenario")
    contract_id = "my_test_contract"
    address = "erd1qqqqqqqqqqqqqpgqdmq43snzxutandvqefxgj89r6fh528v9dwnswvgq9t"
    wasm_hash = "5ce403a4f73701481cc15b2378cdc5bce3e35fa215815aa5eb9104d9f7ab2451"
    _scenario_data = ScenarioData.get()
    _scenario_data.add_contract_data(
        InternalContractData(
            contract_id=contract_id,
            address=address,
            serializer=None,
            wasm_hash=wasm_hash,
            deploy_time=1,
            last_upgrade_time=1,
            saved_values=dict(),
        )
    )

    yield _scenario_data
    delete_scenario_data("pytest_scenario", ask_confirmation=False)
