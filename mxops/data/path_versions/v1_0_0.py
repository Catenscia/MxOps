"""
author: Etienne Wallet

This module contains the classes and the functions used to manage
the data for the data model version 1.0.0

General structure
mxops
└── <data_version>
    └── <network>
        └── scenarios
            └── <scenario_name>
                ├── logs
                ├── checkpoints
                │   └── <checkpoint_name>
                │       ├── abis
                │       └── data.json
                └── current
                    ├── abis
                    └── data.json

"""

import os
from pathlib import Path
import platform

from appdirs import AppDirs
from multiversx_sdk import Address

from mxops.config.config import Config
from mxops.data.path_versions.msc import version_name_to_version_path_name
from mxops.enums import NetworkEnum

VERSION = "v1.0.0"


def get_mxops_data_path() -> Path:
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
        data_path = Path(data_path_config)
    else:
        app_dirs = AppDirs("mxops", "Catenscia")
        data_path = Path(app_dirs.user_data_dir)
    return data_path / version_name_to_version_path_name(VERSION)


def is_current_saved_version() -> bool:
    """
    Check if the current data version saved is the v1.0.0

    :return: version number
    :rtype: str
    """
    file_path = get_mxops_data_path().parent / "VERSION"
    if not file_path.exists():
        return False
    saved_version = file_path.read_text()
    return saved_version == VERSION


def register_as_current() -> bool:
    """
    Check if the current data version saved is the v1.0.0

    :return: version number
    :rtype: str
    """
    file_path = get_mxops_data_path().parent / "VERSION"
    file_path.write_text(VERSION)


def get_root_scenario_data_path(scenario_name: str) -> Path:
    """
    Return the root path for a scenario data, where all data
    (current, checkpoints, logs) will be saved

    :param scenario_name: name of the scenario
    :type scenario_name: str
    :return: path to the root scenario folder
    :rtype: Path
    """
    mxops_data_path = get_mxops_data_path()
    network = Config.get_config().get_network()
    return mxops_data_path / network.name / "scenarios" / scenario_name


def get_scenario_current_path(scenario_name: str) -> Path:
    """
    Return the path of the folder where the data related to the contracts, the tokens,
    the saved values or the abis are written

    :param scenario_name: name of the scenario
    :type scenario_name: str
    :return: folder path
    :rtype: Path
    """
    root_scenario_path = get_root_scenario_data_path(scenario_name)
    return root_scenario_path / "current"


def get_scenario_current_data_path(scenario_name: str) -> Path:
    """
    Return the path of the file where the data related to the contracts, the tokens
    or the saved values are written

    :param scenario_name: name of the scenario
    :type scenario_name: str
    :return: file path
    :rtype: Path
    """
    return get_scenario_current_path(scenario_name) / "data.json"


def get_scenario_current_abis_path(scenario_name: str) -> Path:
    """
    Return the path of the folder where the abis related to
    the contracts of the scenario are saved

    :param scenario_name: name of the scenario
    :type scenario_name: str
    :return: folder path
    :rtype: Path
    """
    return get_scenario_current_path(scenario_name) / "abis"


def get_contract_abi_file_path(scenario_name: str, contract_address: Address) -> Path:
    """
    Return the file path for a contract abi in the current data of a scenario

    :param scenario_name: name of the scenario
    :type scenario_name: str
    :param contract_address: address of the contract
    :type contract_address: Address
    :return: folder path
    :rtype: Path
    """
    folder_path = get_scenario_current_abis_path(scenario_name)
    return folder_path / f"{contract_address.to_bech32()}.abi.json"


def get_scenario_checkpoint_path(scenario_name: str, checkpoint_name: str) -> Path:
    """
    Return the path of the folder where a checkpoint of scenario data has been saved.
    (abis, contracts data, tokens data ...)

    :param scenario_name: name of the scenario
    :type scenario_name: str
    :param scenario_name: name of the checkpoint
    :type scenario_name: str
    :return: folder path
    :rtype: Path
    """
    root_scenario_path = get_root_scenario_data_path(scenario_name)
    return root_scenario_path / "checkpoints" / checkpoint_name


def get_scenario_checkpoint_data_path(scenario_name: str, checkpoint_name: str) -> Path:
    """
    Return the checkpoint path of the file where the data related to the contracts,
    the tokens or the saved values are written

    :param scenario_name: name of the scenario
    :type scenario_name: str
    :param scenario_name: name of the checkpoint
    :type scenario_name: str
    :return: file path
    :rtype: Path
    """
    return get_scenario_checkpoint_path(scenario_name, checkpoint_name) / "data.json"


def get_checkpoint_contract_abi_file_path(
    scenario_name: str, checkpoint_name: str, contract_address: Address
) -> Path:
    """
    Return the file path for a contract abi in the checkpoint data of a scenario

    :param scenario_name: name of the scenario
    :type scenario_name: str
    :param scenario_name: name of the checkpoint
    :type scenario_name: str
    :param contract_address: address of the contract
    :type contract_address: Address
    :return: folder path
    :rtype: Path
    """
    folder_path = get_scenario_checkpoint_path(scenario_name, checkpoint_name) / "abis"
    return folder_path / f"{contract_address.to_bech32()}.abi.json"


def get_mxops_logs_folders() -> Path:
    """
    Return the folder path where to save all the logs of MxOps

    :return: logs folder path
    :rtype: Path
    """
    return get_mxops_data_path() / "logs"


def get_scenario_logs_folder(scenario_name: str) -> Path:
    """
    Return the folder path where to save all execution logs
    for a scenario

    :param scenario_name: name of the scenario
    :type scenario_name: str
    :return: logs folder path
    :rtype: Path
    """
    root_scenario_path = get_root_scenario_data_path(scenario_name)
    return root_scenario_path / "logs"


def get_all_scenarios_names() -> list[str]:
    """
    Return all the scenarios names that have locally saved data in the current network

    :return: list of scenario names
    :rtype: list[str]
    """
    scenarios_folder = get_root_scenario_data_path("fake_scenario").parent
    try:
        elements = os.listdir(scenarios_folder)
    except FileNotFoundError:
        return []

    return [e for e in elements if (scenarios_folder / e).is_dir()]


def get_all_checkpoints_names(scenario_name: str) -> list[str]:
    """
    Return all the existing checkpoints for a given scenario

    :param scenario_name: name of the scenario
    :type scenario_name: str
    :return: list of the existing checkpoints
    :rtype: list[str]
    """
    checkpoints_folder = get_scenario_checkpoint_path(
        scenario_name, "checkpoint"
    ).parent
    try:
        elements = os.listdir(checkpoints_folder)
    except FileNotFoundError:
        return []

    return [e for e in elements if (checkpoints_folder / e).is_dir()]


def does_scenario_exist(scenario_name: str) -> bool:
    """
    Check the data saved locally to tell if the provided scenario already exists

    :param scenario_name: scenario to look for
    :type scenario_name: str
    :return: if the scenario exists
    :rtype: bool
    """
    scenario_root_path = get_root_scenario_data_path(scenario_name)
    return scenario_root_path.exists()


def get_data_cache_file_path(file_name: str, network: NetworkEnum | None) -> Path:
    """
    Return the path to a file containing cache data

    :param file_name: name of the file
    :type file_name: str
    :param network: related to the data, defaults to None which will be current network
    :type network: str
    :return: path to the cache file
    :rtype: Path
    """
    mxops_data_path = get_mxops_data_path()
    if network is None:
        network = Config.get_config().get_network()
    return mxops_data_path / network.name / "cache" / file_name
