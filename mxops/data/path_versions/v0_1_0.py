"""
author: Etienne Wallet

This module contains the classes and the functions used to manage
the data for the data model version 1.0.0

General structure
mxops
└── <network>
        └── <scenario_name><sep><checkpoint_name>.json

"""

import os
from pathlib import Path
import platform

from appdirs import AppDirs

from mxops.config.config import Config
from mxops.enums import NetworkEnum

VERSION = "v0.1.0"
CHECKPOINT_SEP = "___CHECKPOINT___"


def get_data_path() -> Path:
    """
    Return the folder path where to store the data created by this project.
    Is defined in first instance by the value 'DATA_PATH' from the config
    If this value is 'None' or '', a folder will be created in the App Dir
    It uses the library appdirs to follow the conventions
    across multi OS(MAc, Linux, Windows)
    https://pypi.org/project/appdirs/

    :return: path of the folder to use for data saving
    :rtype: Path
    """
    if platform.system() == "Linux":  # handle snap issues
        os.environ["XDG_DATA_HOME"] = os.path.expanduser("~/.local/share")
    config = Config.get_config()
    data_path_config = config.get("DATA_PATH")
    if data_path_config not in ("None", ""):
        return Path(data_path_config)
    app_dirs = AppDirs("mxops", "Catenscia")
    return Path(app_dirs.user_data_dir)


def is_current_saved_version() -> bool:
    """
    Check if the current data version saved is the v0.1.0
    This is the only version without a version file

    :return: version number
    :rtype: str
    """
    file_path = get_data_path() / "VERSION"
    return file_path.parent.exists() and not file_path.exists()


def get_scenario_full_name(scenario_name: str, checkpoint: str = "") -> str:
    """
    Construct the full name of a scenario with contains the name of the scenario
    and potentially the checkpoint separator and the checkpoint

    :param scenario_name: name of the scenario
    :type scenario_name: str
    :param checkpoint: name of the checkpoint, defaults to ""
    :type checkpoint: str, optional
    :return: full name of the scenario
    :rtype: str
    """
    if checkpoint == "":
        return scenario_name
    return f"{scenario_name}{CHECKPOINT_SEP}{checkpoint}"


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
        txs_dir_path = network_path / "transactions"
        try:
            os.makedirs(txs_dir_path.as_posix())
        except FileExistsError:
            pass


def get_scenario_file_path(scenario_name: str, checkpoint_name: str = "") -> Path:
    """
    Construct and return the path of a scenario file:
    <AppDir>/<Network>/<scenario_name>[<checkpoint_separator><checkpoint_name>].json

    :param scenario_name: name of the scenario
    :type scenario_name: str
    :param checkpoint_name: name of the checkpoint, defaults to ''
    :type checkpoint_name: str
    :return: path to the specified scenario file
    :rtype: Path
    """
    data_path = get_data_path()
    config = Config.get_config()
    network = config.get_network()
    scenario_full_name = get_scenario_full_name(scenario_name, checkpoint_name)
    return data_path / network.name / f"{scenario_full_name}.json"


def get_all_scenarios_names() -> list[str]:
    """
    Return all the scenarios names that have locally saved data in the current network

    :return: list of scenario names
    :rtype: list[str]
    """
    config = Config.get_config()
    network = config.get_network()
    data_path = get_data_path()
    files = os.listdir(data_path / network.name)

    return [
        file[:-5]
        for file in files
        if file.endswith(".json") and CHECKPOINT_SEP not in file
    ]


def get_all_checkpoints_names(scenario_name: str) -> list[str]:
    """
    Return all the existing checkpoint for a given scenario

    :param scenario_name: name of the scenario
    :type scenario_name: str
    :return: list of the existing checkpoints
    :rtype: list[str]
    """
    config = Config.get_config()
    network = config.get_network()
    data_path = get_data_path()
    files = os.listdir(data_path / network.name)
    prefix = scenario_name + CHECKPOINT_SEP
    prefix_len = len(prefix)
    return [
        file[prefix_len:-5]
        for file in files
        if file.startswith(prefix) and file.endswith(".json")
    ]


def get_tx_file_path(contract_bech32_address: str) -> Path:
    """
    Construct and return the path of a the file that will contains the transactions
    of a contract.

    :param contract_bech32_address: bech32 address of the contract
    :type contract_bech32_address: str
    :return: path to the save file
    :rtype: Path
    """
    data_path = get_data_path()
    config = Config.get_config()
    network = config.get_network()
    return (
        data_path
        / network.name
        / "transactions"
        / f"{contract_bech32_address}_txs.json"
    )
