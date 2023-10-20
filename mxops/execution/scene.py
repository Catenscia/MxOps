"""
author: Etienne Wallet

This module contains the functions to execute a scene in a scenario
"""
from dataclasses import dataclass, field
import os
from pathlib import Path
import re
from typing import Dict, List

import yaml

from mxops.config.config import Config
from mxops.data.execution_data import _ScenarioData, ExternalContractData, ScenarioData
from mxops.execution.steps import LoopStep, SceneStep, Step, instanciate_steps
from mxops.execution.account import AccountsManager
from mxops import errors
from mxops.utils.logger import get_logger


LOGGER = get_logger("scene")


@dataclass
class Scene:
    """
    Dataclass to represent a set of step to execute sequentially
    within a scenario.
    """

    allowed_networks: List[str]
    allowed_scenario: List[str]
    accounts: List[Dict] = field(default_factory=list)
    steps: List[Step] = field(default_factory=list)
    external_contracts: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        """
        After the initialisation of an instance, if the inner steps are
        found to be Dict, will try to convert them to Steps instances.
        Usefull for easy loading from yaml files
        """
        if len(self.steps) > 0 and isinstance(self.steps[0], Dict):
            self.steps = instanciate_steps(self.steps)


def load_scene(path: Path) -> Scene:
    """
    Load a scene file and convert its content into a list

    :param path: _description_
    :type path: Path
    :return: _description_
    :rtype: List[Step]
    """
    with open(path.as_posix(), "r", encoding="utf-8") as file:
        raw_scene = yaml.safe_load(file)

    return Scene(**raw_scene)


def execute_scene(scene_path: Path):
    """
    Load and execute a scene

    :param scene_path: path to the scene file
    :type scene_path: Path
    """
    LOGGER.info(f"Executing scene {scene_path}")
    scene = load_scene(scene_path)
    scenario_data = ScenarioData.get()

    config = Config.get_config()
    network = config.get_network()

    # check network authorization
    if (
        network.name not in scene.allowed_networks
        and network.value not in scene.allowed_networks
    ):
        raise errors.ForbiddenSceneNetwork(
            scene_path, network.value, scene.allowed_networks
        )

    # check scenario authorizations
    match_found = False
    for scenario_pattern in scene.allowed_scenario:
        if re.match(scenario_pattern, scenario_data.name) is not None:
            match_found = True
            break
    if not match_found:
        raise errors.ForbiddenSceneScenario(
            scene_path, scenario_data.name, scene.allowed_scenario
        )

    # load accounts
    for account in scene.accounts:
        AccountsManager.load_account(**account)
        AccountsManager.sync_account(account["account_name"])

    # load external contracts addresses
    for contract_id, address in scene.external_contracts.items():
        try:
            # try to update the contract address while keeping data intact
            scenario_data.set_contract_value(contract_id, "address", address)
        except errors.UnknownContract:
            # otherwise create the contract data
            scenario_data.add_contract_data(
                ExternalContractData(
                    contract_id=contract_id, address=address, saved_values={}
                )
            )

    # execute steps
    for step in scene.steps:
        execute_step(step, scenario_data)


def execute_step(step: Step, scenario_data: _ScenarioData):
    """
    Execute a step

    :param step: step to execute
    :type step: Step
    :param scenario_data: data of the current Scenario
    :type scenario_data: _ScenarioData
    """
    if isinstance(step, SceneStep):
        execute_scene(Path(step.scene_path))
    elif isinstance(step, LoopStep):
        for sub_step in step.generate_steps():
            execute_step(sub_step, scenario_data)
    else:
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
