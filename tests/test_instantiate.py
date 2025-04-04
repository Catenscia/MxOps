from pathlib import Path

import yaml

from mxops.data.execution_data import ScenarioData
from mxops.execution.checks.factory import instanciate_checks
from mxops.execution.scene import execute_scene, load_scene
from mxops.execution.steps import (
    ContractCallStep,
    ContractDeployStep,
    ContractQueryStep,
    ContractUpgradeStep,
)
from mxops.execution.steps.factory import instanciate_steps
from tests.utils import instantiate_assert_all_args_provided


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
            checks=[
                {
                    "type": "Success",
                },
            ],
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
            results_save_keys=["TokenIdentifier"],
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
        {"account_id": "owner", "pem_path": "wallets/local_owner.pem"},
        {
            "abi_path": "tests/data/abis/adder.abi.json",
            "account_id": "adder",
            "address": "erd1qqqqqqqqqqqqqpgqfj3z3k4vlq7dc2928rxez0uhhlq46s6p4mtqerlxhc",
        },
    ]
    assert scene.allowed_networks == ["localnet"]
    assert scene.allowed_scenario == [".*"]


def test_abi_loading(test_data_folder_path: Path):
    # Given
    scene_path = test_data_folder_path / "scenes" / "empty_scene.yaml"
    scenario_data = ScenarioData.get()

    # When
    execute_scene(scene_path)
    contract_abi = scenario_data.get_contract_raw_abi("adder")

    # Then
    assert set(e["name"] for e in contract_abi["endpoints"]) == {
        "getSum",
        "upgrade",
        "add",
    }


def test_default_loading(test_data_folder_path: Path):
    # Given
    scene_path = test_data_folder_path / "scenes" / "default_scene.yaml"

    # When
    scene = load_scene(scene_path)

    # Then
    assert len(scene.steps) == 0
    assert len(scene.accounts) == 0
    assert scene.allowed_networks == [
        "devnet",
        "testnet",
        "localnet",
        "chain-simulator",
    ]
    assert scene.allowed_scenario == [".*"]


def test_bytes_loading_and_conversion(test_data_folder_path: Path):
    # Given
    scene_path = test_data_folder_path / "scenes" / "bytes_scene.yaml"
    scene = load_scene(scene_path)

    # When
    for step in scene.steps:
        step.evaluate_smart_values()
        if not isinstance(step, ContractCallStep):
            raise ValueError(f"Wrong type loaded: {type(step)}")
        tx = step.build_unsigned_transaction()
        assert tx.data == b"endpoint_1@01020408"


def test_instantiate_all_steps(test_data_folder_path: Path):
    # Given
    file_path = test_data_folder_path / "all_steps.yaml"
    with open(file_path.as_posix(), "r", encoding="utf-8") as file:
        content = yaml.safe_load(file)
    raw_steps = content["steps"]

    # When
    steps = instanciate_steps(raw_steps)

    # Then
    for raw_step, step in zip(raw_steps, steps):
        raw_step.pop("type")
        instantiate_assert_all_args_provided(
            step.__class__, raw_step, arguments_to_ignore={"checks"}
        )


def test_instantiate_all_checks(test_data_folder_path: Path):
    # Given
    file_path = test_data_folder_path / "all_checks.yaml"
    with open(file_path.as_posix(), "r", encoding="utf-8") as file:
        content = yaml.safe_load(file)
    raw_checks = content["checks"]

    # When
    checks = instanciate_checks(raw_checks)

    # Then
    for raw_check, check in zip(raw_checks, checks):
        raw_check.pop("type")
        instantiate_assert_all_args_provided(check.__class__, raw_check)
