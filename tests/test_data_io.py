import json
from pathlib import Path

import pytest

from mxops.data.data import _ScenarioData, InternalContractData, TokenData
from mxops.enums import NetworkEnum, TokenTypeEnum


@pytest.mark.parametrize(
    'scenario_path',
    [
        Path('tests/data/scenarios/scenario_A.json'),
        Path('tests/data/scenarios/scenario_B.json'),
    ]
)
def test_scenario_loading(scenario_path: Path):
    """
    Test that contract data is correctly loaded and that both environment syntax are handeld
    """
    # Given
    # When
    scenario = _ScenarioData.load_from_path(scenario_path)

    # Then
    assert scenario.network == NetworkEnum.DEV
    assert scenario.name == "mxops_tutorial_first_scene"
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


def test_token_data_loading():
    """
    Test that token data is correctly loaded
    """
    # Given
    scenario_path = Path('tests/data/scenarios/scenario_C.json')

    # When
    scenario = _ScenarioData.load_from_path(scenario_path)

    # Then
    assert scenario.tokens_data == {
        'My Token': TokenData(
            name='My Token',
            ticker='MTK',
            identifier='MTK-abcdef',
            saved_values={},
            type=TokenTypeEnum.FUNGIBLE
        )
    }


def test_io_unicity():
    """
    Test the loading and writing are consistent
    """
    # Given
    scenario_path = Path('tests/data/scenarios/scenario_C.json')
    with open(scenario_path.as_posix(), encoding='utf-8') as file:
        raw_data = json.load(file)

    # When
    scenario = _ScenarioData.load_from_path(scenario_path)
    scenario_dict = scenario.to_dict()

    # Then
    print('result:', json.dumps(scenario_dict, indent=4))
    print('expected:', json.dumps(raw_data, indent=4))
    assert scenario_dict == raw_data
