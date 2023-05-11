"""
author: Etienne Wallet

This module contains the functions to load, write and update contracts data
"""
from __future__ import annotations
from dataclasses import asdict, dataclass, field, is_dataclass
import json
import os
from pathlib import Path
import time
from typing import Any, Dict, Optional

from mxops.config.config import Config
from mxops.data.path import get_scenario_file_path
from mxops import enums as mxops_enums
from mxops import errors
from mxops.utils.logger import get_logger


LOGGER = get_logger('data')


@dataclass
class SavedValuesData:
    """
    Dataclass representing an object that can store values for the environment
    """
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

    def get_value(self, value_key: str) -> Any:
        """
        Fetch a value from the attribute of the class or from the saved value

        :param value_key: key for the value
        :type value_key: str
        :return: value saved under the attribute or the the key provided
        :rtype: Any
        """
        try:
            return getattr(self, value_key)
        except AttributeError:
            pass
        return self.get_saved_value(value_key)

    def get_saved_value(self, value_key: str) -> Any:
        """
        Fetch a value saved under a key

        :param value_key: key for the value
        :type value_key: str
        :return: value saved under the key
        :rtype: Any
        """
        try:
            return self.saved_values[value_key]
        except KeyError as err:
            raise ValueError(
                f'Unkown key: {value_key} for data object {self}') from err


@dataclass
class ContractData(SavedValuesData):
    """
    Dataclass representing the data that can be locally saved for a contract
    """
    contract_id: str
    address: str

    def set_value(self, value_key: str, value: Any):
        """
        Set the a value under a specified key

        :param value_key: key to save the value
        :type value_key: str
        :param value: value to save
        :type value: Any
        """
        if value_key == 'address':
            self.address = value
        else:
            super().set_value(value_key, value)

    def to_dict(self) -> Dict:
        """
        Convert this instance to a dictionary

        :return: this instance as a dictionary
        :rtype: Dict
        """
        self_dict = asdict(self)
        # add attribute to indicate internal/external
        self_dict['is_external'] = isinstance(self, ExternalContractData)
        return self_dict


@dataclass
class InternalContractData(ContractData):
    """
    Dataclass representing the data that can be locally saved for a contract
    managed by MxOps
    """
    wasm_hash: str
    deploy_time: int
    last_upgrade_time: int


@dataclass
class ExternalContractData(ContractData):
    """
    Dataclass representing the data that can be locally saved for a contract
    not managed by MxOps
    """


@dataclass
class TokenData(SavedValuesData):
    """
    Dataclass representing a token issued on MultiversX
    """
    name: str
    ticker: str
    identifier: str
    type: mxops_enums.TokenTypeEnum

    def to_dict(self) -> Dict:
        """
        Transform this instance to a dictionnary

        :return: dictionary representing this instance
        :rtype: Dict
        """
        self_dict = asdict(self)
        self_dict['type'] = self.type.value
        return self_dict

    @classmethod
    def from_dict(cls, data: Dict) -> TokenData:
        """
        Create an instance of TokenData from a dictionary

        :param data: dictionary to transform into TokenData
        :type data: Dict
        :return: instance from the input dictionary
        :rtype: TokenData
        """
        formated_data = {
            'type': mxops_enums.parse_token_type_enum(data['type'])
        }
        return cls(**{**data, **formated_data})


@dataclass
class _ScenarioData:
    """
    Dataclass representing the data that can be locally saved for a scenario
    """
    name: str
    network: mxops_enums.NetworkEnum
    creation_time: int
    last_update_time: int
    contracts_data: Dict[str, ContractData] = field(default_factory=dict)
    tokens_data: Dict[str, TokenData] = field(default_factory=dict)

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
        return contract.get_value(value_key)

    def set_contract_value(self, contract_id: str, value_key: str, value: Any):
        """
        Set the value of a contract for a given key

        :param contract_id: unique id of the contract in the scenario
        :type contract_id: str
        :param value_key: key for the value to set
        :type value_key: str
        """
        self._set_update_time()
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
        self._set_update_time()
        if contract_data.contract_id in self.contracts_data:
            raise errors.ContractIdAlreadyExists(contract_data.contract_id)
        self.contracts_data[contract_data.contract_id] = contract_data

    def get_token_value(self, token_name: str, value_key: str) -> Any:
        """
        Return the value of a token for a given key

        :param token_name: unique name of the token in the scenario
        :type token_name: str
        :param value_key: key for the value to fetch
        :type value_key: str
        :return: value saved under the given key
        :rtype: Any
        """
        try:
            token_data = self.tokens_data[token_name]
        except KeyError as err:
            raise errors.UnknownToken(self.name, token_name) from err
        return token_data.get_value(value_key)

    def set_token_value(self, token_name: str, value_key: str, value: Any):
        """
        Set the value of a contract for a given key

        :param token_name: unique name of the token in the scenario
        :type token_name: str
        :param value_key: key for the value to set
        :type value_key: str
        """
        self._set_update_time()
        try:
            token_data = self.tokens_data[token_name]
        except KeyError as err:
            raise errors.UnknownToken(self.name, token_name) from err
        token_data.set_value(value_key, value)
        self.save()

    def add_token_data(self, token_data: TokenData):
        """
        Add a token data to the scenario

        :param contract_data: data to add to the scenario
        :type contract_data: ContractData
        """
        self._set_update_time()
        if token_data.name in self.tokens_data:
            raise errors.TokenNameAlreadyExists(token_data.name)
        self.tokens_data[token_data.name] = token_data

    def get_value(self, root_name: str, value_key: str) -> Any:
        """
        Search within tokens data and contracts data the value saved under the provided key

        :param root_name: contract id or token name that hosts the value
        :type root_name: str
        :param value_key: key under which the value is savedd
        :type value_key: str
        :return: value saved
        :rtype: Any
        """
        try:
            return self.get_contract_value(root_name, value_key)
        except errors.UnknownContract:
            pass

        try:
            return self.get_token_value(root_name, value_key)
        except errors.UnknownToken:
            pass
        raise errors.UnknownRootName(self.name, root_name)

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
        for key, value in self_dict.items():
            if isinstance(value, dict):
                self_dict[key] = {}
                for sub_key, sub_value in value.items():
                    try:
                        self_dict[key][sub_key] = sub_value.to_dict()
                        continue
                    except AttributeError:
                        pass
                    if is_dataclass(sub_value):
                        self_dict[key][sub_key] = asdict(sub_value)
                    else:
                        self_dict[key][sub_key] = sub_value
        self_dict['network'] = self.network.value
        return self_dict

    def _set_update_time(self):
        """
        Set the last update time to now
        """
        self.last_update_time = int(time.time())

    @classmethod
    def load_from_name(cls, scenario_name: str) -> _ScenarioData:
        """
        Retrieve the locally saved scenario data and instantiate it

        :param scenario_name: name of the scenario to load
        :type scenario_name: str
        :return: loaded scenario data
        :rtype: _ScenarioData
        """
        scenario_path = get_scenario_file_path(scenario_name)
        return cls.load_from_path(scenario_path)

    @classmethod
    def load_from_path(cls, scenario_path: Path) -> _ScenarioData:
        """
        Retrieve the locally saved scenario data and instantiate it

        :param scenario_path: path to the scenario to load
        :type scenario_path: Path
        :return: loaded scenario data
        :rtype: _ScenarioData
        """
        with open(scenario_path.as_posix(), 'r', encoding='utf-8') as file:
            raw_content = json.load(file)
        return cls.from_dict(raw_content)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> _ScenarioData:
        """
        Create an instance of _ScenarioData from a dict

        :param data: data with the needed attributes and values
        :type data: Dict[str, Any]
        :return: _ScenarioData instance corresponding to the provided data
        :rtype: ScenarioData
        """
        contracts_data = {}
        for contract_id, contract_data in data['contracts_data'].items():
            if isinstance(contract_data, Dict):
                try:
                    is_external = contract_data.pop('is_external')
                except KeyError:
                    is_external = False
                if is_external:
                    contracts_data[contract_id] = ExternalContractData(**contract_data)
                else:
                    contracts_data[contract_id] = InternalContractData(**contract_data)

        tokens_data = data.get('tokens_data', {})
        tokens_data = {k: TokenData.from_dict(v) for k, v in tokens_data.items()}

        formated_data = {
            'contracts_data': contracts_data,
            'tokens_data': tokens_data,
            'network': mxops_enums.parse_network_enum(data['network'])
        }

        return cls(**{**data, **formated_data})


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
            cls._instance = _ScenarioData.load_from_name(scenario_name)
        except FileNotFoundError as err:
            raise errors.UnknownScenario(scenario_name) from err
        config = Config.get_config()
        network = config.get_network()
        LOGGER.info((f'Scenario {scenario_name} loaded for '
                     f'network {network.value}'))

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
                     f'network {network.value}'))


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
        LOGGER.info(f'The data of the scenario {scenario_name} has been deleted')
    except FileNotFoundError:
        LOGGER.warning((f'The scenario {scenario_name} does'
                        ' not have any data recorded'))
