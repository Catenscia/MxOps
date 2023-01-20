"""
author: Etienne Wallet

This module (input/output) contains the functions to load and write contracts data
"""
import os
from pathlib import Path
from typing import List

from appdirs import AppDirs

from mxops.config.config import Config
from mxops.enums import NetworkEnum
from mxops.utils.logger import get_logger


LOGGER = get_logger('data-IO')


def get_data_path() -> Path:
    """
    Return the folder path where to store the data created by this project.
    The folder will be created if it does not exists.
    It uses the library appdirs to follow the conventions across multi OS(MAc, Linux, Windows)
    https://pypi.org/project/appdirs/

    :return: path of the folder to use for data saving
    :rtype: Path
    """
    app_dirs = AppDirs("mxops", "Catenscia")
    data_path = Path(app_dirs.user_data_dir)
    return data_path


def initialize_data_folder():
    """
    Create the necessary folders to save locally the scenario data
    """
    data_path = get_data_path()
    for network in NetworkEnum:
        network_path = data_path / network.name
        try:
            os.makedirs(network_path.as_posix())
        except FileExistsError:
            pass


def get_scenario_file_path(scenario_name: str) -> Path:
    """
    Construct and return the path of a scenario file:
    <AppDir>/<Network>/<scenario_name>.json

    :param scenario_name: _description_
    :type scenario_name: str
    :return: path to the specified scenario file
    :rtype: Path
    """
    data_path = get_data_path()
    config = Config.get_config()
    network = config.get_network()
    return data_path / network.name / f'{scenario_name}.json'


def get_all_scenarios_names() -> List[str]:
    """
    Return all the scenarios names that have locally saved data in the current network

    :return: list of scenario names
    :rtype: List[str]
    """
    config = Config.get_config()
    network = config.get_network()
    data_path = get_data_path()
    files = os.listdir(data_path / network.name)

    return [file[:-5] for file in files if file.endswith('.json')]


LOGGER.debug(f'MxOps app directory is located at {get_data_path()}')
