from pathlib import Path

import pytest

from mxops.data.data import _ScenarioData, InternalContractData
from mxops.enums import NetworkEnum


@pytest.mark.parametrize(
    'scenario_path',
    [
        Path('tests/data/scenarios/scenario_A.json'),
        Path('tests/data/scenarios/scenario_B.json')
    ]
)
def test_scenario_loading(scenario_path: Path):
    # Given
    # When
    scenario = _ScenarioData.load_from_path(scenario_path)

    # Then
    assert scenario.network == NetworkEnum.DEV
    assert scenario.name == "mxops_tutorial_first_scene"
    print(type(scenario.contracts_data), scenario.contracts_data)
    assert scenario.contracts_data == {
        "egld-ping-pong": InternalContractData(
            contract_id="egld-ping-pong",
            address="erd1qqqqqqqqqqqqqpgq0048vv3uk6l6cdreezpallvduy4qnfv2plcq74464k",
            saved_values={},
            wasm_hash="5ce403a4f73701481cc15b2378cdc5bce3e35fa215815aa5eb9104d9f7ab2451",
            deploy_time=1677134892,
            last_upgrade_time=1677134892
        )
    }
