"""
author: Etienne Wallet

This module contains the functions to load, write and update scenario data

"""

from __future__ import annotations
from copy import deepcopy
from dataclasses import asdict, dataclass, field, is_dataclass
import json
import logging
import os
from pathlib import Path
import re
import shutil
import sys
import time
from typing import Any

from multiversx_sdk import Address
from multiversx_sdk.abi import Abi, AbiDefinition
from multiversx_sdk.core.errors import BadAddressError

from mxops.config.config import Config
from mxops.data import data_path
from mxops.enums import (
    LogGroupEnum,
    NetworkEnum,
    TokenTypeEnum,
    parse_network_enum,
    parse_token_type_enum,
)
from mxops import errors
from mxops.data.utils import json_dump, json_load
from mxops.utils.logger import get_logger

LOGGER = get_logger(LogGroupEnum.DATA)


def parse_value_key(path) -> list[int | str]:
    """
    Parse a value key string into keys and indices using regex.

    e.g. "key_1.key2[2].data" -> ['key_1', 'key2', 2, 'data']
    """
    # This regex captures:
    # - words, possibly including hyphens
    # - numbers within square brackets
    pattern = r"([\w\-]+)|\[(\d+)\]"
    tokens = re.findall(pattern, path)

    # Flatten the list and convert indices to int
    return [int(index) if index else key for key, index in tokens]


def parse_raw_saved_values_data_data(raw_data: dict) -> SavedValuesData:
    """
    Parse raw data into a SavedValuesData or one of its subclasses

    :param raw_data: data to parse
    :type raw_data: dict
    :return: instance
    :rtype: SavedValuesData
    """
    data_copy = deepcopy(raw_data)
    class_name = data_copy.pop("__class__")
    current_module = sys.modules[__name__]
    class_type = getattr(current_module, class_name)
    if not issubclass(class_type, SavedValuesData):
        raise ValueError(f"Exepted a SavedValuesData class, got {class_type}")
    return class_type.from_dict(data_copy)


@dataclass(kw_only=True)
class SavedValuesData:
    """
    Dataclass representing an object that can store nested values for the scenario
    """

    saved_values: dict[str, Any] = field(default_factory=dict)

    def _get_element_value_from_key(self, element: Any, key: str | int) -> Any:
        """
        Fetch the value of the element using a key

        :param element: element to explore
        :type element: Any
        :param key: key of the value to fetch
        :type key: str | int
        :return: fetched value
        :rtype: Any
        """
        if not isinstance(key, (int, str)):
            raise TypeError(f"Key must be an int or a str, got {type(key)}")
        if isinstance(element, (tuple, list)):
            key = int(key)
            return element[key]
        if isinstance(element, dict):
            try:
                return element[key]
            except KeyError:
                pass
            try:
                if isinstance(key, int):
                    key = str(key)
                else:
                    key = int(key)
            except ValueError:
                pass
            return element[key]
        raise TypeError(
            f"Element must be a dict, a list or a tuple, got {type(element)}"
        )

    def _get_element(self, parsed_value_key_path: list[str | int]) -> Any:
        """
        Get the value saved under the specified value key path.


        :param parsed_value_key_path: parsed elements of a value key path
        :type parsed_value_key_path: list[str | int]
        :return: element saved under the value key path
        :rtype: Any
        """
        if len(parsed_value_key_path) == 0:
            raise errors.WrongDataKeyPath("Key path is empty")

        # check if the wanted element is an attribute of the instance
        if len(parsed_value_key_path) == 1:
            value_key = parsed_value_key_path[0]
            if isinstance(value_key, str) and hasattr(self, value_key):
                return getattr(self, value_key)

        # other fetch it from the saved values
        element = self.saved_values
        for key in parsed_value_key_path:
            try:
                element = self._get_element_value_from_key(element, key)
            except (KeyError, IndexError, ValueError) as err:
                element_str = str(element)
                if len(element_str) > 1000:
                    element_str = element_str[:500] + "..." + element_str[-500:]
                raise errors.WrongDataKeyPath(
                    f"Wrong key {repr(key)} from keys {parsed_value_key_path} for "
                    f"data element {element_str}"
                ) from err
        return element

    def set_value(self, value_key_path: str, value: Any):
        """
        Set the a value under a specified value key path

        :param value_key_path: value key of the value to fetch
        :type value_key_path: str
        :param value: value to save
        :type value: Any
        """
        parsed_value_key = parse_value_key(value_key_path)
        element = self.saved_values

        if len(parsed_value_key) == 0:
            raise errors.WrongDataKeyPath("Key path is empty")

        # verify the path and create it if necessary
        if len(parsed_value_key) == 1:
            next_key = parsed_value_key[0]
        else:
            for key, next_key in zip(parsed_value_key[:-1], parsed_value_key[1:]):
                if isinstance(key, int):
                    if isinstance(element, list):
                        element_size = len(element)
                        if key > element_size:
                            raise errors.WrongDataKeyPath(
                                f"Tried to set element {key} of a list but the list"
                                f" has only {element_size} elements: {element}"
                            )
                        if key == element_size:
                            element.append(  # pylint: disable=E1101
                                [] if isinstance(next_key, int) else {}
                            )
                        element = element[key]
                    else:
                        raise errors.WrongDataKeyPath(
                            f"Expected a list but found {element}"
                        )
                else:
                    if isinstance(element, dict):
                        try:
                            element = element[key]
                        except KeyError:  # key does not exist yet
                            element[key] = [] if isinstance(next_key, int) else {}
                            element = element[key]
                    else:
                        raise errors.WrongDataKeyPath(
                            f"Expected a dict but found {element}"
                        )

        # set the value
        value_copy = deepcopy(value)  # in case the value is a complex type
        if isinstance(next_key, int):
            if isinstance(element, (tuple, list)):
                try:
                    element[next_key] = value_copy
                except IndexError as err:
                    if next_key > len(element):
                        raise errors.WrongDataKeyPath(
                            f"Tried to set element {next_key} of a list but the list "
                            f"has only {len(element)} elements: {element}"
                        ) from err
                    element.append(value_copy)
            else:
                raise errors.WrongDataKeyPath(
                    f"Expected a tuple or a list but found {element}"
                )
        else:
            if isinstance(element, dict):
                element[next_key] = value_copy
            else:
                raise errors.WrongDataKeyPath(f"Expected a dict but found {element}")

    def get_value(self, value_key_path: str) -> Any:
        """
        Fetch a value from the attribute of the class or from the saved value

        :param value_key_path: key path for the value
        :type value_key_path: str
        :return: value saved under the attribute or the value key provided
        :rtype: Any
        """
        try:
            return getattr(self, value_key_path)
        except AttributeError:
            pass
        parsed_value_key = parse_value_key(value_key_path)
        return self._get_element(parsed_value_key)

    def to_dict(self) -> dict:
        """
        Transform this instance to a dictionnary

        :return: dictionary representing this instance
        :rtype: dict
        """
        self_dict = asdict(self)
        self_dict["__class__"] = self.__class__.__name__
        return self_dict

    @classmethod
    def from_dict(cls, data: dict) -> SavedValuesData:
        """
        Transform data into an instance of this class or subclass

        :return: instance of this class of subclass
        :rtype: SavedValuesData
        """
        return cls(**data)

    def __eq__(self, other: Any) -> bool:
        """
        Define the equal operator

        :param other: object to compare this instance with
        :type other: Any
        :return: if the instance is equal to the other object
        :rtype: bool
        """
        if not isinstance(other, SavedValuesData):
            raise ValueError(f"Can not compare {type(self)} with {type(other)}")
        return self.to_dict() == other.to_dict()


@dataclass
class AccountData(SavedValuesData):
    """
    Dataclass representing the data that can be locally saved for an account
    """

    account_id: str
    bech32: str

    def get_value(self, value_key_path: str) -> Any:
        """
        Fetch a value from the attribute of the class or from the saved value

        :param value_key_path: key path for the value
        :type value_key_path: str
        :return: value saved under the attribute or the value key provided
        :rtype: Any
        """
        if value_key_path == "address":
            value_key_path = "bech32"
        elif value_key_path == "contract_id":
            value_key_path = "account_id"
        return super().get_value(value_key_path)


@dataclass
class ContractData(AccountData):
    """
    Dataclass representing the data that can be locally saved for a contract
    It is supposed to be inherited from and not use directly
    """

    @classmethod
    def from_dict(cls, data: dict) -> ContractData:
        """
        Transform data into an instance of this class or subclass

        :return: instance of this class of subclass
        :rtype:
        """
        data_copy = deepcopy(data)
        if "contract_id" in data:
            data_copy["account_id"] = data_copy.pop("contract_id")
        return super().from_dict(data_copy)

    def get_value(self, value_key_path: str) -> Any:
        """
        Fetch a value from the attribute of the class or from the saved value

        :param value_key_path: key path for the value
        :type value_key_path: str
        :return: value saved under the attribute or the value key provided
        :rtype: Any
        """
        if value_key_path == "contract_id":
            value_key_path = "account_id"
        return super().get_value(value_key_path)


@dataclass
class InternalContractData(ContractData):
    """
    Dataclass representing the data that can be locally saved for a contract
    managed by MxOps
    """

    code_hash: str
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
    type: TokenTypeEnum

    def to_dict(self) -> dict:
        """
        Transform this instance to a dictionnary

        :return: dictionary representing this instance
        :rtype: dict
        """
        self_dict = super().to_dict()
        self_dict["type"] = self.type.value
        return self_dict

    @classmethod
    def from_dict(cls, data: dict) -> TokenData:
        """
        Create an instance of TokenData from a dictionary

        :param data: dictionary to transform into TokenData
        :type data: dict
        :return: instance from the input dictionary
        :rtype: TokenData
        """
        formated_data = {"type": parse_token_type_enum(data["type"])}
        return super().from_dict({**data, **formated_data})


@dataclass
class PemAccountData(AccountData):
    """
    Defines the data of a user account defined with a PEM
    """

    pem_path: str


@dataclass
class LedgerAccountData(AccountData):
    """
    Defines the data of a user account defined with a ledger
    """

    ledger_address_index: int


@dataclass
class _ScenarioData(SavedValuesData):
    """
    Dataclass representing the data that can be locally saved for a scenario
    """

    name: str
    network: NetworkEnum
    creation_time: int
    last_update_time: int
    accounts_data: dict[str, AccountData] = field(default_factory=dict)
    account_id_to_bech32: dict[str, str] = field(default_factory=dict)
    tokens_data: dict[str, TokenData] = field(default_factory=dict)
    _abi_cache: dict[str, dict] = field(default_factory=dict, init=False)

    def get_account_data(self, designation: str | Address) -> AccountData:
        """
        Using the stored contracts, return a contract from a contract id,
        a bech32 or an address

        :param designation: designation of the contract
        :type designation: str | Address
        :return: data of the account
        :rtype: AddrAccountDataess
        """
        account_address = self.get_account_address(designation)
        try:
            return self.accounts_data[account_address.to_bech32()]
        except KeyError as err:
            raise errors.UnknownAccount(self.name, designation) from err

    def get_account_address(self, designation: str | Address) -> Address:
        """
        Using the stored account, return an account address from a contract id,
        a bech32 or an address

        :param designation: designation of the contract
        :type designation: str | Address
        :return: address of the account
        :rtype: Address
        """
        if isinstance(designation, Address):
            return designation
        try:
            return Address.new_from_bech32(designation)
        except BadAddressError:
            pass
        try:
            bech32 = self.account_id_to_bech32[designation]
            return Address.new_from_bech32(bech32)
        except (KeyError, BadAddressError) as err:
            raise errors.UnknownAccount(self.name, designation) from err

    def get_account_value(self, designation: Address | str, value_key: str) -> Any:
        """
        Return the value of an account for a given key

        :param designation: address or id of the contract in the scenario
        :type designation: Address | str
        :param value_key: key for the value to fetch
        :type value_key: str
        :return: value saved under the given key
        :rtype: Any
        """
        account_bech32 = self.get_account_address(designation).to_bech32()
        try:
            account = self.accounts_data[account_bech32]
        except KeyError as err:
            raise errors.UnknownAccount(self.name, designation) from err
        return account.get_value(value_key)

    def get_contract_raw_abi(
        self, designation: Address | str, use_cache: bool = True
    ) -> dict:
        """
        Return the dictionary of a contract abi given its designation.
        Look first if it exists in the cache, else try to search for
        it in the Scenario locally saved data

        :param designation: address or id of the contract to get the ABI of
        :type designation: designation: Address | str
        :param use_cache: if the abi cache should be used, default to True
        :type use_cache: bool
        :return: abi of the contract as a json
        :rtype: dict
        """
        contract_address = self.get_account_address(designation)
        contract_bech32 = contract_address.to_bech32()
        if use_cache:
            try:
                return self._abi_cache[contract_bech32]
            except KeyError:
                pass
        file_path = data_path.get_contract_abi_file_path(self.name, contract_address)
        try:
            content = file_path.read_text()
        except FileNotFoundError as err:
            raise errors.UnknownAbiContract(self.name, contract_address) from err
        contract_abi = json.loads(content)
        self._abi_cache[contract_bech32] = contract_abi
        return contract_abi

    def get_contract_abi(
        self, contract_designation: Address | str, use_cache: bool = True
    ) -> Abi:
        """
        Return the Abi instance of a contract abi given its address or id.
        Look first if it exists in the cache, else try to search for
        it in the Scenario locally saved data

        :param contract_address: address or id of the contract to get the abi of
        :type contract_address: Address | str
        :param use_cache: if the abi cache should be used, default to True
        :type use_cache: bool
        :return: abi of the contract
        :rtype: Abi
        """
        return Abi(
            AbiDefinition.from_dict(
                self.get_contract_raw_abi(contract_designation, use_cache)
            )
        )

    def set_contract_abi_from_source(
        self, contract_designation: Address | str, abi_path: Path
    ):
        """
        Return the dictionary of a contract abi given its address or id.
        Look first if it exists in the cache, else try to search for
        it in the Scenario locally saved data

        :param contract_designation: address or id of the contract to get the abi of
        :type contract_designation: Address | str
        :return: abi of the contract as a json
        :rtype: dict
        """
        contract_address = self.get_account_address(contract_designation)
        file_path = data_path.get_contract_abi_file_path(self.name, contract_address)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(abi_path, file_path)
        _ = self.get_contract_raw_abi(contract_address, use_cache=False)  # update cache

    def set_account_value(
        self, account_designation: Address | str, value_key_path: str, value: Any
    ):
        """
        Set the value of an account for a given key path

        :param contract_address: address or id of the contract in the scenario
        :type contract_address: Address | str
        :param value_key_path: key path for the value to set
        :type value_key_path: str
        """
        account_address = self.get_account_address(account_designation)
        account_bech32 = account_address.to_bech32()
        try:
            account = self.accounts_data[account_bech32]
        except KeyError as err:
            raise errors.UnknownAccount(self.name, account_address) from err
        account.set_value(value_key_path, value)
        self._set_update_time()
        self.save()

    def add_account_data(self, account_data: AccountData):
        """
        Add the data of an account to the scenario

        :param account_data: data to add to the scenario
        :type account_data: AccountData
        """
        existing_bech32 = self.account_id_to_bech32.get(account_data.account_id, None)
        if existing_bech32 is not None and existing_bech32 != account_data.bech32:
            raise errors.AccoundIdAlreadyhasBech32(
                account_data.account_id, existing_bech32, account_data.bech32
            )
        if account_data.bech32 in self.accounts_data:
            existing_id = self.accounts_data[account_data.bech32].account_id
            if existing_id != account_data.account_id:
                raise errors.AccountAlreadyHasId(
                    account_data.bech32,
                    self.accounts_data[account_data.bech32].account_id,
                    account_data.account_id,
                )
        self.account_id_to_bech32[account_data.account_id] = account_data.bech32
        self.accounts_data[account_data.bech32] = account_data
        self._set_update_time()
        self.save()

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

    def set_token_value(self, token_name: str, value_key_path: str, value: Any):
        """
        Set the value of a contract for a given key

        :param token_name: unique name of the token in the scenario
        :type token_name: str
        :param value_key_path: key path for the value to set
        :type value_key_path: str
        """
        self._set_update_time()
        try:
            token_data = self.tokens_data[token_name]
        except KeyError as err:
            raise errors.UnknownToken(self.name, token_name) from err
        token_data.set_value(value_key_path, value)
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

    def get_value(self, value_key_path: str) -> Any:
        """
        Search within tokens data, contracts data and scenario saved values,
        the value saved under the provided key

        :param value_key_path: key path under which the value is savedd
        :type value_key_path: str
        :return: value saved
        :rtype: Any
        """
        parsed_value_key = parse_value_key(value_key_path)
        if len(parsed_value_key) > 1:
            root_name = parsed_value_key[0]
            value_sub_key = value_key_path[len(root_name) + 1 :]  # remove also the dot
            try:
                return self.get_account_value(root_name, value_sub_key)
            except errors.UnknownAccount:
                pass
            try:
                return self.get_token_value(root_name, value_sub_key)
            except errors.UnknownToken:
                pass
        return super().get_value(value_key_path)

    def set_value(self, value_key_path: str, value: Any):
        """
        Set the a value under a specified value key path

        :param value_key_path: value key path of the value to fetch
        :type value_key_path: str
        :param value: value to save
        :type value: Any
        """
        parsed_value_key = parse_value_key(value_key_path)
        if len(parsed_value_key) > 1:
            root_name = parsed_value_key[0]
            value_sub_key = value_key_path[len(root_name) + 1 :]  # remove also the dot
            try:
                return self.set_account_value(root_name, value_sub_key, value)
            except errors.UnknownAccount:
                pass
            try:
                return self.set_token_value(root_name, value_sub_key, value)
            except errors.UnknownToken:
                pass
        return super().set_value(value_key_path, value)

    def save(self):
        """
        Save this scenario as the current data
        Overwrite any existing data
        """
        data_file_path = data_path.get_scenario_current_data_path(self.name)
        data_file_path.parent.mkdir(parents=True, exist_ok=True)
        json_dump(data_file_path, self.to_dict())

    def to_dict(self) -> dict:
        """
        Convert this instance to a dictionary

        :return: this instance as a dictionary
        :rtype: dict
        """
        self_dict = {**self.__dict__}
        for key in list(self_dict.keys()):
            if key.startswith("_"):
                self_dict.pop(key)
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
        self_dict["network"] = self.network.value
        return self_dict

    def _set_update_time(self):
        """
        Set the last update time to now
        """
        self.last_update_time = int(time.time())

    @classmethod
    def load_from_name(
        cls, scenario_name: str, checkpoint_name: str = ""
    ) -> _ScenarioData:
        """
        Retrieve the locally saved scenario data and instantiate it

        :param scenario_name: name of the scenario to load
        :type scenario_name: str
        :param checkpoint_name: name of the checkpoint of the scenario to load
        :type checkpoint_name: str
        :return: loaded scenario data
        :rtype: _ScenarioData
        """
        if checkpoint_name != "":
            data_file_path = data_path.get_scenario_checkpoint_data_path(
                scenario_name, checkpoint_name
            )
        else:
            data_file_path = data_path.get_scenario_current_data_path(scenario_name)
        return cls.load_from_path(data_file_path)

    @classmethod
    def load_from_path(cls, scenario_path: Path) -> _ScenarioData:
        """
        Retrieve the locally saved scenario data and instantiate it

        :param scenario_path: path to the scenario to load
        :type scenario_path: Path
        :return: loaded scenario data
        :rtype: _ScenarioData
        """
        raw_content = json_load(scenario_path)
        return cls.from_dict(raw_content)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> _ScenarioData:
        """
        Create an instance of _ScenarioData from a dict

        :param data: data with the needed attributes and values
        :type data: dict[str, Any]
        :return: _ScenarioData instance corresponding to the provided data
        :rtype: ScenarioData
        """
        accounts_data = data.get("accounts_data", {})
        accounts_data = {
            k: parse_raw_saved_values_data_data(v) for k, v in accounts_data.items()
        }

        tokens_data = data.get("tokens_data", {})
        tokens_data = {
            k: parse_raw_saved_values_data_data(v) for k, v in tokens_data.items()
        }

        formated_data = {
            "accounts_data": accounts_data,
            "tokens_data": tokens_data,
            "network": parse_network_enum(data["network"]),
        }

        return cls(**{**data, **formated_data})


class ScenarioData:  # pylint: disable=too-few-public-methods
    """
    Shell class that implement the singleton logic for the _ScenarioData
    class.
    Only one scenario should be loaded by execution.
    """

    _instance: _ScenarioData | None = None

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
    def load_scenario(cls, scenario_name: str, checkpoint_name: str = ""):
        """
        Load scenario data singleton.

        :param scenario_name: name of the scenario to load
        :type scenario_name: str
        :param checkpoint_name: name of the checkpoint of the scenario to load
        :type checkpoint_name: str
        """
        if cls._instance is not None:
            raise errors.UnloadedScenario
        try:
            cls._instance = _ScenarioData.load_from_name(scenario_name, checkpoint_name)
        except FileNotFoundError as err:
            raise errors.UnknownScenario(scenario_name) from err
        config = Config.get_config()
        network = config.get_network()
        if cls._instance.name != scenario_name:
            # inconsistency may happen due to cloning of scenario
            # the source of truth is the folder name
            cls._instance.name = scenario_name
        LOGGER.info(f"scenario {scenario_name} loaded for network {network.value}")

    @classmethod
    def create_scenario(cls, scenario_name: str, overwrite: bool = False):
        """
        Create a scenario data while checking for a pre existing instance.

        :param scenario_name: name of the scenario to create
        :type scenario_name: str
        :param overwrite: if existing scenario should be overwritten
                        defaults to False
        :type overwrite: bool
        """
        if data_path.does_scenario_exist(scenario_name):
            message = (
                "A scenario already exists under the name "
                f"{scenario_name}. Do you want to override it? (y/n)"
            )
            if not overwrite and input(message).lower() not in ("y", "yes"):
                raise errors.ScenarioNameAlreadyExists(scenario_name)
            delete_scenario_data(scenario_name, ask_confirmation=False)

        config = Config.get_config()
        network = config.get_network()
        current_timestamp = int(time.time())
        cls._instance = _ScenarioData(
            scenario_name, network, current_timestamp, current_timestamp, {}
        )
        LOGGER.info((f"Scenario {scenario_name} created for network {network.value}"))

    @classmethod
    def get_scenario_logger(cls, logger_group: LogGroupEnum) -> logging.Logger:
        """
        Return a logger dedicated to a logging group in the current scenario
        if no current scenario is defined, raise an error

        :return: logger
        :rtype: logging.Logger
        """
        if cls._instance is None:
            raise errors.UnloadedScenario
        return get_logger(
            logger_group,
            data_path.get_scenario_logs_folder(cls._instance.name) / "scenario.log",
        )


def delete_scenario_data(
    scenario_name: str, checkpoint_name: str = "", ask_confirmation: bool = True
):
    """
    Delete locally saved data for a given scenario

    :param scenario_name: name of the scenario to delete
    :type scenario_name: str
    :param checkpoint_name: name of the checkpoint to delete. If not specified, all the
        checkpoints and the current scenario data will be deleted.
    :type checkpoint_name: str
    :param ask_confirmation: if a deletion confirmation should be asked,
                             defaults to True
    :type ask_confirmation: bool
    """
    network = Config.get_config().get_network()
    if checkpoint_name == "":
        root_scenario_path = data_path.get_root_scenario_data_path(scenario_name)
        LOGGER.info(f"Deletion of the scenario {scenario_name} on {network.value}")
        if ask_confirmation:
            message = (
                "Confirm the deletion of the data related to the scenario "
                f"{scenario_name} on {network.value}. This includes"
                "all the checkpoints previously saved for this scenario: (y/n)? "
            )
            if input(message).lower() not in ("y", "yes"):
                LOGGER.info("User aborted deletion")
                return
        try:
            shutil.rmtree(root_scenario_path)
            LOGGER.info("Scenario deleted")
        except FileNotFoundError:
            LOGGER.warning(f"Scenario {scenario_name} on {network.value} do not exist")
    else:
        checkpoint_folder_path = data_path.get_scenario_checkpoint_path(
            scenario_name, checkpoint_name
        )
        LOGGER.info(
            f"Deletion of the checkpoint {checkpoint_name} for the scenario "
            f"{scenario_name} on {network.value}"
        )
        if ask_confirmation:
            message = (
                "Confirm the deletion of the data related to the checkpoint "
                f"{checkpoint_name} of the scenario {scenario_name} on {network.value}"
            )
            if input(message).lower() not in ("y", "yes"):
                LOGGER.info("User aborted deletion")
                return
        try:
            shutil.rmtree(checkpoint_folder_path)
            LOGGER.info("Checkpoint deleted")
        except FileNotFoundError:
            LOGGER.warning(
                f"Checkpoint {checkpoint_name} for scenario {scenario_name} "
                f"on {network.value} do not exist"
            )


def create_scenario_data_checkpoint(scenario_name: str, checkpoint_name: str):
    """
    Create a checkpoint of the current data of a scenario

    :param scenario_name: name of the scenario to save
    :type scenario_name: str
    :param checkpoint_name: name of the checkpoint to create
    :type checkpoint_name: str
    """
    source_path = data_path.get_scenario_current_path(scenario_name)
    destination_path = data_path.get_scenario_checkpoint_path(
        scenario_name, checkpoint_name
    )
    network = Config.get_config().get_network()
    LOGGER.info(
        f"Creating checkpoint {checkpoint_name} for scenario {scenario_name} on "
        f"network {network.value}"
    )

    if os.path.exists(destination_path):
        shutil.rmtree(destination_path)
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source_path, destination_path)
    LOGGER.info("Checkpoint created")


def load_scenario_data_checkpoint(scenario_name: str, checkpoint_name: str):
    """
    Load a previously saved checkpoint as the current data of a scenario

    :param scenario_name: name of the scenario
    :type scenario_name: str
    :param checkpoint_name: name of the checkpoint to load
    :type checkpoint_name: str
    """
    source_path = data_path.get_scenario_checkpoint_path(scenario_name, checkpoint_name)
    destination_path = data_path.get_scenario_current_path(scenario_name)
    network = Config.get_config().get_network()
    LOGGER.info(
        f"Loading checkpoint {checkpoint_name} for scenario {scenario_name} on "
        f"network {network.value}"
    )

    if os.path.exists(destination_path):
        shutil.rmtree(destination_path)
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source_path, destination_path)
    LOGGER.info("Checkpoint loaded")


def clone_scenario_data(
    source_scenario_name: str,
    destination_scenario_name: str,
    ask_confirmation: bool = True,
):
    """
    Clone locally save data for a given scenario to another one

    :param source_scenario_name: name of the scenario to copy
    :type source_scenario_name: str
    :param destination_scenario_name: name of the scenario that will be a copy
    :type destination_scenario_name: str
    :param ask_confirmation: if a clone confirmation should be asked,
                             defaults to True
    :type ask_confirmation: bool
    """
    source_path = data_path.get_root_scenario_data_path(source_scenario_name)
    destination_path = data_path.get_root_scenario_data_path(destination_scenario_name)
    network = Config.get_config().get_network()
    LOGGER.info(
        f"Cloning scenario {source_scenario_name} into "
        f"scenario {destination_scenario_name}"
    )
    if ask_confirmation:
        message = (
            f"Confirm the copy of the {network.value} scenario {source_scenario_name} "
            f"to overwrite any data for scenario {destination_scenario_name}. (y/n)"
        )
        if input(message).lower() not in ("y", "yes"):
            LOGGER.info("User aborted copy")
            return

    if os.path.exists(destination_path):
        shutil.rmtree(destination_path)
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source_path, destination_path)
    LOGGER.info(
        f"The data of the scenario {source_scenario_name} has been cloned to "
        f"scenario {destination_scenario_name}"
    )
