from pathlib import Path

from mxpyserializer.abi_serializer import AbiSerializer

from mxops.data.execution_data import ScenarioData
from mxops.execution.checks import SuccessCheck
from mxops.execution.scene import execute_scene, load_scene
from mxops.execution.steps import (
    ContractCallStep,
    ContractDeployStep,
    ContractQueryStep,
    ContractUpgradeStep,
)


def test_deploy_scene_instantiation(test_data_folder_path: Path):
    # Given
    scene_path = test_data_folder_path / "scenes" / "deploy_scene.yaml"

    # When
    scene = load_scene(scene_path)
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
        ContractQueryStep(
            endpoint="getTokenIdentifier",
            contract="SEGLD-minter",
            arguments=[],
            results_save_keys=["TokenIdentifier"],
            results_types=[{"type": "TokenIdentifier"}],
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


def test_abi_loading(test_data_folder_path: Path):
    # Given
    scene_path = test_data_folder_path / "scenes" / "empty_scene.yaml"
    scenario_data = ScenarioData.get()

    # When
    execute_scene(scene_path)
    serializer: AbiSerializer = scenario_data.get_contract_value("adder", "serializer")

    # Then
    assert list(serializer.endpoints.keys()) == ["getSum", "upgrade", "add", "init"]


def test_default_loading(test_data_folder_path: Path):
    # Given
    scene_path = test_data_folder_path / "scenes" / "default_scene.yaml"

    # When
    scene = load_scene(scene_path)

    # Then
    assert len(scene.steps) == 0
    assert len(scene.accounts) == 0
    assert len(scene.external_contracts) == 0
    assert scene.allowed_networks == [
        "devnet",
        "testnet",
        "localnet",
        "chain-simulator",
    ]
    assert scene.allowed_scenario == [".*"]
