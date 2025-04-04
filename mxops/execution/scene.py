"""
author: Etienne Wallet

This module contains the functions to execute a scene in a scenario
"""

from dataclasses import dataclass, field
import os
from pathlib import Path
import re

from multiversx_sdk import Address
import yaml

from mxops.config.config import Config
from mxops.data.execution_data import (
    _ScenarioData,
    AccountData,
    ExternalContractData,
    ScenarioData,
)
from mxops.enums import LogGroupEnum
from mxops.execution.account import AccountsManager
from mxops import errors
from mxops.execution.steps import LoopStep, SceneStep
from mxops.execution.steps.base import Step
from mxops.execution.steps.factory import instanciate_steps


def get_default_allowed_networks() -> list[str]:
    """
    Return the network that are allowed by default on a scene

    :return: names of the allowed networks
    :rtype: list[str]
    """
    return ["devnet", "testnet", "localnet", "chain-simulator"]


def get_default_allowed_scenarios() -> list[str]:
    """
    Return the scenarios that are allowed by default on a scene

    :return: regex of the allowed scenarios
    :rtype: list[str]
    """
    return [".*"]


@dataclass
class Scene:
    """
    Dataclass to represent a set of step to execute sequentially
    within a scenario.
    """

    allowed_networks: list[str] = field(default_factory=get_default_allowed_networks)
    allowed_scenario: list[str] = field(default_factory=get_default_allowed_scenarios)
    accounts: list[dict] = field(default_factory=list)
    steps: list[Step] = field(default_factory=list)

    def __post_init__(self):
        """
        After the initialisation of an instance, if the inner steps are
        found to be dict, will try to convert them to Steps instances.
        useful for easy loading from yaml files
        """
        if len(self.steps) > 0 and isinstance(self.steps[0], dict):
            self.steps = instanciate_steps(self.steps)


def load_scene(path: Path) -> Scene:
    """
    Load a scene file and convert its content into a list

    :param path: _description_
    :type path: Path
    :return: _description_
    :rtype: list[Step]
    """
    with open(path.as_posix(), "r", encoding="utf-8") as file:
        raw_scene = yaml.safe_load(file)

    if raw_scene is None:
        raw_scene = {}

    return Scene(**raw_scene)


def parse_load_account(account: dict):
    """
    Parse and load account data provided by the user in a scene.
    The account will either be passed to the Scenario data or to the account manager
    depending on the account type

    :param account: account data of a scene
    :type account: dict
    """
    # first, load signing accounts
    if "folder_path" in account:
        AccountsManager.load_register_pem_from_folder(**account)
        return
    if "ledger" in account:
        AccountsManager.load_register_ledger_account(**account)
        return
    if "pem" in account:
        AccountsManager.load_register_pem_account(**account)
        return

    # now handle user and external accounts
    # account id and bech32 parameters mush be provided
    if "account_id" in account:
        account_id = account["account_id"]
    elif "contract_id" in account:
        account_id = account["contract_id"]
    else:
        raise errors.InvalidSceneDefinition(
            f"Account {account} is missing the `account_id` parameter"
        )
    if "bech32" in account:
        bech32 = account["bech32"]
    elif "address" in account:
        bech32 = account["address"]
    else:
        raise errors.InvalidSceneDefinition(
            f"Account {account} is missing the `address` or `bech32` parameter"
        )
    address = Address.new_from_bech32(bech32)
    scenario_data = ScenarioData.get()
    if address.is_smart_contract():
        scenario_data.add_account_data(ExternalContractData(account_id, bech32))
        if "abi_path" in account:
            scenario_data.set_contract_abi_from_source(
                Address.new_from_bech32(bech32), Path(account["abi_path"])
            )
    else:
        scenario_data.add_account_data(AccountData(account_id, bech32))


def execute_scene(path: Path):
    """
    Load and execute a scene

    :param path: path to the scene file
    :type path: Path
    """
    logger = ScenarioData.get_scenario_logger(LogGroupEnum.EXEC)
    logger.info(f"Executing scene {path}")
    scene = load_scene(path)
    scenario_data = ScenarioData.get()

    config = Config.get_config()
    network = config.get_network()

    # check network authorization
    if (
        network.name not in scene.allowed_networks
        and network.value not in scene.allowed_networks
    ):
        raise errors.ForbiddenSceneNetwork(path, network.value, scene.allowed_networks)

    # check scenario authorizations
    match_found = False
    for scenario_pattern in scene.allowed_scenario:
        if re.match(scenario_pattern, scenario_data.name) is not None:
            match_found = True
            break
    if not match_found:
        raise errors.ForbiddenSceneScenario(
            path, scenario_data.name, scene.allowed_scenario
        )

    # load accounts
    for account in scene.accounts:
        parse_load_account(account)

    # execute steps
    for step in scene.steps:
        execute_step(step, scenario_data)


def execute_scene_step(step: SceneStep):
    """
    Execute the scene step according to its parameters


    :param step: step describing a scene execution
    :type step: SceneStep
    """
    step.evaluate_smart_values()
    for _ in range(step.repeat.get_evaluated_value()):
        # reevaluate in the loop in case the scene modify its own values
        step.evaluate_smart_values()
        path = step.path.get_evaluated_value()
        if path.is_file():
            execute_scene(path)
        else:
            execute_directory(path)


def execute_step(step: Step, scenario_data: _ScenarioData):
    """
    Execute a step

    :param step: step to execute
    :type step: Step
    :param scenario_data: data of the current Scenario
    :type scenario_data: _ScenarioData
    """
    if isinstance(step, SceneStep):
        execute_scene_step(step)
    elif isinstance(step, LoopStep):
        for sub_step in step.generate_steps():
            execute_step(sub_step, scenario_data)
    else:
        step.evaluate_smart_values()
        step.execute()
        scenario_data.save()


def execute_directory(directory_path: Path):
    """
    Load and execute scenes from a directory

    :param directory_path: path to the directory containing the files
    :type directory_path: Path
    """
    files = sorted(os.listdir(directory_path.as_posix()))
    for file in files:
        file_path = directory_path / file
        if os.path.isfile(file_path):
            execute_scene(directory_path / file)
