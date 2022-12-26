from xops.execution.scene import Scene
from xops.execution.steps import ContractCallStep, ContractDeployStep, ContractQueryStep


def test_deploy_scene_instantiation(deploy_yaml_content):
    # Given

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
            wait_for_result=True
        ),
        ContractCallStep(
            'SEGLD-minter',
            'owner',
            'setTokenLocalRoles',
            80000000,
            wait_for_result=True
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
