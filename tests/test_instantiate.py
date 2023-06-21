from pathlib import Path
import yaml
from mxops.execution.checks import SuccessCheck

from mxops.execution.scene import Scene
from mxops.execution.steps import (
    ContractCallStep,
    ContractDeployStep,
    ContractQueryStep,
    ContractUpgradeStep,
)


def test_deploy_scene_instantiation(test_data_folder_path: Path):
    # Given
    with open(test_data_folder_path / "deploy_scene.yaml", encoding="utf-8") as file:
        deploy_yaml_content = yaml.safe_load(file)

    # When
    scene = Scene(**deploy_yaml_content)
    loaded_steps = scene.steps

    # Then
    expected_steps = [
        ContractDeployStep(
            sender="owner",
            wasm_path="../contract/src/esdt-minter/output/esdt-minter.wasm",
            contract_id="SEGLD-minter",
            gas_limit=80000000,
            upgradeable=True,
            readable=False,
            payable=False,
            payable_by_sc=False,
            arguments=[125000000, 120],
        ),
        ContractCallStep(
            sender="owner",
            contract="SEGLD-minter",
            endpoint="registerToken",
            gas_limit=80000000,
            arguments=["SEGLD", "SEGLD", 18],
            value="&BASE_ISSUING_COST",
            checks=[SuccessCheck()],
        ),
        ContractCallStep(
            sender="owner",
            contract="SEGLD-minter",
            endpoint="setTokenLocalRoles",
            gas_limit=80000000,
            checks=[],
        ),
        ContractQueryStep(
            endpoint="getTokenIdentifier",
            contract="SEGLD-minter",
            arguments=[],
            expected_results=[{"save_key": "TokenIdentifier", "result_type": "str"}],
            print_results=True,
        ),
        ContractUpgradeStep(
            sender="owner",
            wasm_path="../contract/src/esdt-minter/output/esdt-minter.wasm",
            contract="SEGLD-minter",
            gas_limit=50000000,
            upgradeable=True,
            readable=False,
            payable=True,
            payable_by_sc=True,
            arguments=[200],
        ),
    ]

    assert expected_steps == loaded_steps
    assert scene.accounts == [
        {"account_name": "owner", "pem_path": "wallets/local_owner.pem"}
    ]
    assert scene.allowed_networks == ["localnet"]
    assert scene.allowed_scenario == [".*"]
