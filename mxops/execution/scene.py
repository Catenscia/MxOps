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
from mxops.data.data import ScenarioData
from mxops.execution.steps import Step, instanciate_steps
from mxops.execution.account import AccountsManager
from mxops import errors
from mxops.utils.logger import get_logger


LOGGER = get_logger('scene')


@dataclass
class Scene:
    """
    Dataclass to represent a set of step to execute sequentially
    within a scenario.
    """
    allowed_networks: List[str]
    allowed_scenario: List[str]
    accounts: List[Dict] = field(default_factory=lambda: [])
    steps: List[Step] = field(default_factory=lambda: [])

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
    with open(path.as_posix(), 'r', encoding='utf-8') as file:
        raw_scene = yaml.safe_load(file)

    return Scene(**raw_scene)


def execute_scene(scene_path: Path):
    """
    Load and execute a scene

    :param scene_path: path to the scene file
    :type scene_path: Path
    """
    LOGGER.info(f'Executing scene {scene_path}')
    scene = load_scene(scene_path)
    scenario_data = ScenarioData.get()

    config = Config.get_config()
    network = config.get_network()

    # check network authorization
    if network.name not in scene.allowed_networks:
        raise errors.ForbiddenSceneNetwork(
            scene_path,
            network.name,
            scene.allowed_networks
        )

    # check scenario authorizations
    match_found = False
    for scenario_pattern in scene.allowed_scenario:
        if re.match(scenario_pattern, scenario_data.name) is not None:
            match_found = True
            break
    if not match_found:
        raise errors.ForbiddenSceneScenario(
            scene_path,
            scenario_data.name,
            scene.allowed_scenario
        )

    # load accounts
    for account in scene.accounts:
        AccountsManager.load_account(**account)
        AccountsManager.sync_account(account['account_name'])

    # execute steps
    for step in scene.steps:
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
