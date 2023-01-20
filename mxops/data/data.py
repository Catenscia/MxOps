"""
author: Etienne Wallet

This module contains the functions to load, write and update contracts data
"""
from __future__ import annotations
from dataclasses import dataclass
import json
import os
from pathlib import Path
import time
from typing import Any, Dict, Optional
from mxops.config.config import Config
from mxops.data.path import get_scenario_file_path

from mxops.enums import NetworkEnum
from mxops import errors
from mxops.utils.logger import get_logger


LOGGER = get_logger('data')


@dataclass
class ContractData:
    """
    Dataclass representing the data that can be locally saved for a contract
    """
    contract_id: str
    address: str
    wasm_hash: str
    deploy_time: int
    last_upgrade_time: int
    saved_values: Dict[str, Any]

    def set_value(self, value_key: str, value: Any):
        """
        Set the a value under a specified key

        :param value_key: key to save the value
        :type value_key: str
        :param value: value to save
        :type value: Any
        """
        self.saved_values[value_key] = value

    def get_saved_value(self, value_key: str) -> Any:
        """
        Fetch a value saved under a key for this contract

        :param value_key: key for the value
        :type value_key: str
        :return: value saved under the key
        :rtype: Any
        """
        try:
            return self.saved_values[value_key]
        except KeyError as err:
            raise ValueError(
                f'Unkown key: {value_key} for contract {self.contract_id}') from err

    def to_dict(self) -> Dict:
        """
        Convert this instance to a dictionary

        :return: this instance as a dictionary
        :rtype: Dict
        """
        self_dict = {**self.__dict__}
        # avoid shallow copy (warning: not nested proof)
        self_dict['saved_values'] = dict(self_dict['saved_values'])
        return self_dict


@dataclass
class _ScenarioData:
    """
    Dataclass representing the data that can be locally saved for a scenario
    """
    name: str
    network: NetworkEnum
    creation_time: int
    last_update_time: int
    contracts_data: Dict[str, ContractData]

    @staticmethod
    def load_from_file(scenario_name: str) -> _ScenarioData:
        """
        Retrieve the locally saved scenario data and instantiate it

        :param scenario_name: name of the scenario to load
        :type scenario_name: str
        :return: loaded scenario data
        :rtype: _ScenarioData
        """
        scenario_path = get_scenario_file_path(scenario_name)
        with open(scenario_path.as_posix(), 'r', encoding='utf-8') as file:
            return _ScenarioData(**json.load(file))

    def __post_init__(self):
        """
        After the initialisation of an instance, if the contracts data are found to be Dict,
        will try to convert them to ContractData instances.
        Will also try to convert string network to NetworkEnum.
        Usefull for easy loading from json files
        """
        checked_data = {}
        for contract_id, contract_data in self.contracts_data.items():
            if isinstance(contract_data, Dict):
                checked_data[contract_id] = ContractData(**contract_data)
            elif isinstance(contract_data, ContractData):
                checked_data[contract_id] = contract_data
            else:
                raise TypeError(('Unexpected contract data '
                                 f'type {type(contract_data)}'))
        self.contracts_data = checked_data

        if isinstance(self.network, str):
            self.network = NetworkEnum(self.network)

    def get_contract_value(self, contract_id: str, value_key: str) -> Any:
        """
        Return the value of a contract for a given key

        :param contract_id: unique id of the contract in the scenario
        :type contract_id: str
        :param value_key: key for the value to fetch
        :type value_key: str
        :return: value saved under the given key
        :rtype: Any
        """
        try:
            contract = self.contracts_data[contract_id]
        except KeyError as err:
            raise errors.UnknownContract(self.name, contract_id) from err
        try:
            return getattr(contract, value_key)
        except AttributeError:
            pass
        return contract.get_saved_value(value_key)

    def set_contract_value(self, contract_id: str, value_key: str, value: Any):
        """
        Set the value of a contract for a given key

        :param contract_id: unique id of the contract in the scenario
        :type contract_id: str
        :param value_key: key for the value to fetch
        :type value_key: str
        :return: value saved under the given key
        :rtype: Any
        """
        self.last_update_time = int(time.time())
        try:
            contract = self.contracts_data[contract_id]
        except KeyError as err:
            raise errors.UnknownContract(self.name, contract_id) from err
        contract.set_value(value_key, value)
        self.save()

    def add_contract_data(self, contract_data: ContractData):
        """
        Add a contract data to the scenario

        :param contract_data: data to add to the scenario
        :type contract_data: ContractData
        """
        self.last_update_time = int(time.time())
        if contract_data.contract_id in self.contracts_data:
            raise errors.ContractIdAlreadyExists(contract_data.contract_id)
        self.contracts_data[contract_data.contract_id] = contract_data

    def save(self):
        """
        Save this scenario data where it belongs.
        Overwrite any existing file
        """
        scenario_path = get_scenario_file_path(self.name)
        with open(scenario_path.as_posix(), 'w', encoding='utf-8') as file:
            json.dump(self.to_dict(), file)

    def to_dict(self) -> Dict:
        """
        Convert this instance to a dictionary

        :return: this instance as a dictionary
        :rtype: Dict
        """
        self_dict = {**self.__dict__}
        self_dict['network'] = self.network.name
        self_dict['contracts_data'] = {}
        for contract_id, contract_data in self.contracts_data.items():
            self_dict['contracts_data'][contract_id] = contract_data.to_dict()
        return self_dict


class ScenarioData:  # pylint: disable=too-few-public-methods
    """
    Shell class that implement the singleton logic for the _ScenarioData
    class.
    Only one scenario should be loaded by execution.
    """

    _instance: Optional[_ScenarioData] = None

    @classmethod
    def get(cls) -> _ScenarioData:
        """
        Return the already loaded Scenario Data

        :return: scenario data
        :rtype: _ScenarioData
        """
        if cls._instance is None:
            raise errors.UnloadedScenario
        return cls._instance

    @classmethod
    def load_scenario(cls, scenario_name: str):
        """
        Load scenario data singleton.

        :param scenario_name: name of the scenario to load
        :type scenario_name: str
        """
        if cls._instance is not None:
            raise errors.UnloadedScenario
        try:
            cls._instance = _ScenarioData.load_from_file(scenario_name)
        except FileNotFoundError as err:
            raise errors.UnknownScenario(scenario_name) from err
        config = Config.get_config()
        network = config.get_network()
        LOGGER.info((f'Scenario {scenario_name} loaded for '
                     f'network {network.name}'))

    @classmethod
    def create_scenario(cls, scenario_name: str):
        """
        Create a scenario data while checking for a pre existing instance.

        :param scenario_name: name of the scenario to create
        :type scenario_name: str
        """
        if check_scenario_file(scenario_name):
            message = ('A scenario already exists under the name '
                       f'{scenario_name}. Do you want to override it? (y/n)')
            if input(message).lower not in ('y', 'yes'):
                raise errors.ScenarioNameAlreadyExists(scenario_name)

        config = Config.get_config()
        network = config.get_network()
        current_timestamp = int(time.time())
        cls._instance = _ScenarioData(scenario_name,
                                      network,
                                      current_timestamp,
                                      current_timestamp,
                                      {})
        LOGGER.info((f'Scenario {scenario_name} created for '
                     f'network {network.name}'))


def check_scenario_file(scenario_name: str) -> bool:
    """
    Check if a file exists for a given scenario name

    :param scenario_name: name of the scenario to check
    :type scenario_name: str
    :return: if a file exists
    :rtype: bool
    """
    file_path = get_scenario_file_path(scenario_name)
    return Path(file_path).exists()


def delete_scenario_data(scenario_name: str, ask_confirmation: bool = True):
    """
    Delete locally save data for a given scenario

    :param scenario_name: name of the scenario to delete
    :type scenario_name: str
    :param ask_confirmation: if a deletion confirmation should be asked,
                             defaults to True
    :type ask_confirmation: bool
    """
    scenario_path = get_scenario_file_path(scenario_name)
    if ask_confirmation:
        message = (f'Confirm the deletion of the scenario {scenario_name} '
                   f'located at {scenario_path.as_posix()}. (y/n)')
        if input(message).lower() not in ('y', 'yes'):
            print('User aborted deletion')
            return
    try:
        os.remove(scenario_path.as_posix())
    except FileNotFoundError:
        LOGGER.warning((f'The scenario {scenario_name} does'
                        ' not have any data recorded'))
