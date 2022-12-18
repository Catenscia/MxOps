"""
author: Etienne Wallet

This module contains the functions to execute a scene in a scenario
"""
from dataclasses import dataclass
import os
from pathlib import Path
import re
from typing import Dict, List

import yaml

from xops.config.config import Config
from xops.data.data import ScenarioData
from xops.execution import steps
from xops.execution.account import AccountsManager


@dataclass
class Scene:
    """
    Dataclass to represent a set of step to execute sequentially
    within a scenario.
    """
    allowed_networks: List[str]
    allowed_scenario: List[str]
    accounts: List[Dict]
    steps: List[steps.Step]

    def __post_init__(self):
        """
        After the initialisation of an instance, if the inner steps are
        found to be Dict, will try to convert them to Steps instances.
        Usefull for easy loading from yaml files
        """
        if len(self.steps) > 0 and isinstance(self.steps[0], Dict):
            self.steps = steps.instanciate_steps(self.steps)


def load_scene(path: Path) -> Scene:
    """
    Load a scene file and convert its content into a list

    :param path: _description_
    :type path: Path
    :return: _description_
    :rtype: List[steps.Step]
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
    scene = load_scene(scene_path)
    scenario_data = ScenarioData.get()

    config = Config.get_config()
    network = config.get_network()

    # check network authorization
    if network.name not in scene.allowed_networks:
        raise ValueError(('Scene not allowed to be executed '
                          f'in the network {network.name}'))

    # check scenario authorizations
    match_found = False
    for scenario_pattern in scene.allowed_scenario:
        if re.match(scenario_pattern, scenario_data.name) is not None:
            match_found = True
            break
    if not match_found:
        raise ValueError((f'Scene {scene_path} not allowed to be executed '
                          f'in the scenario {scenario_data.name}'))

    # load accounts
    for account in scene.accounts:
        AccountsManager.load_account(**account)

    # execute steps
    for step in scene.steps:
        step.execute()


def execute_directory(directory_path: Path):
    """
    Load and execute scenes from a directory

    :param directory_path: path to the directory containing the files
    :type directory_path: Path
    """
    files = sorted(os.listdir(directory_path.as_posix()))
    for file in files:
        execute_scene(file)
