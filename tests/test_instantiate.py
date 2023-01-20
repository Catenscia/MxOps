from pathlib import Path
import yaml

from mxops.execution.scene import Scene
from mxops.execution.steps import ContractCallStep, ContractDeployStep, ContractQueryStep


def test_deploy_scene_instantiation(test_data_folder_path: Path):
    # Given
    with open(test_data_folder_path / 'deploy_scene.yaml', encoding='utf-8') as file:
        deploy_yaml_content = yaml.safe_load(file)

    # When
    scene = Scene(**deploy_yaml_content)
    loaded_steps = scene.steps

    # Then
    expected_steps = [
        ContractDeployStep(
            'SEGLD-minter',
            'owner',
            '../contract/src/esdt-minter/output/esdt-minter.wasm',
            80000000,
            True,
            False,
            False,
            False,
            [125000000, 120]
        ),
        ContractCallStep(
            'SEGLD-minter',
            'owner',
            'registerToken',
            80000000,
            ['SEGLD', 'SEGLD', 18],
            '&BASE_ISSUING_COST',
            check_for_errors=True
        ),
        ContractCallStep(
            'SEGLD-minter',
            'owner',
            'setTokenLocalRoles',
            80000000,
            check_for_errors=True
        ),
        ContractQueryStep(
            'SEGLD-minter',
            'getTokenIdentifier',
            [],
            [{'save_key': 'TokenIdentifier', 'result_type': 'str'}],
            True
        )
    ]

    assert expected_steps == loaded_steps
    assert scene.accounts == [
        {'account_name': 'owner', 'pem_path': 'wallets/local_owner.pem'}]
    assert scene.allowed_networks == ['LOCAL']
    assert scene.allowed_scenario == ['.*']
