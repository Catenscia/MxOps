"""
author: Etienne Wallet

This module contains utils functions related to path navigation
"""

from configparser import ConfigParser
import os
from pathlib import Path

from importlib_resources import files
from multiversx_sdk import ProxyNetworkProvider
from multiversx_sdk.network_providers.resources import NetworkConfig

from mxops.enums import NetworkEnum


class _Config:
    """
    Utility class that reads a config file and serves its parameters.
    """

    def __init__(self, network: NetworkEnum, config_path: Path | None = None):
        """
        Initialise the configuration instance by reading the specified config file.

        :param network: which network is to be considered when reading the config values
        :type network: NetworkEnum
        :param config_path: path to the config file
        :type config_path: Path
        """
        self.__network = network
        self.__config = ConfigParser()

        if config_path is not None:
            with open(config_path.as_posix(), "r", encoding="utf-8") as config_file:
                self.__config.read_file(config_file)
        else:
            default_config = files("mxops.resources").joinpath("default_config.ini")
            self.__config.read_string(default_config.read_text())

        self.__network_config: NetworkConfig | None = None

    def set_network(self, network: NetworkEnum):
        """
        Set the network enum

        :param network: network enum to set
        :type network: NetworkEnum
        """
        self.__network = network
        self.__network_config = None

    def get_network(self) -> NetworkEnum:
        """
        Return the network of the config

        :return: network used
        :rtype: NetworkEnum
        """
        return self.__network

    def get_network_config(self) -> NetworkConfig:
        """
        Return the loaded network config

        :return: network config
        :rtype: NetworkConfig
        """
        if self.__network_config is None:
            # cannot use MyProxyNetworkProvider
            # due to circular dependencies
            self.__network_config = ProxyNetworkProvider(
                self.get("PROXY")
            ).get_network_config()
        return self.__network_config

    def get(self, option: str, network: NetworkEnum | None = None) -> str:
        """
        return the specified option for the current environment
        or a specified environment

        :param option: option to get from the config file
        :type option: str
        :param network: netowrk to get the option of, default to None wich is current
        :type network: NetworkEnum | None
        :return: value for the option as a string
        :rtype: str
        """
        if network is None:
            network_name = self.__network.name
        else:
            network_name = network.name
        return self.__config.get(network_name, option)

    def get_options(self) -> list[str]:
        """
        Return the options for the current environment

        :return: list of available options for the current env
        :rtype: list[str]
        """
        return [o.upper() for o in self.__config.options(self.__network.name)]

    def get_values(self) -> dict[str, str]:
        """
        Return all the values of the options for the current environment

        :return: dictionary with option:value for the current env
        :rtype: dict[str, str]
        """
        options = self.get_options()
        return {o: self.get(o) for o in options}

    def set_option(self, option: str, value: str):
        """
        Set a value for an option in the current environment

        :param option: name of the option
        :type option: str
        :param value: value for the option
        :type value: str
        """
        self.__config.set(self.__network.name, option, value)


class Config:
    """
    Singleton class that serves the _Config class
    """

    __instance: _Config | None = None
    __network: NetworkEnum = NetworkEnum.LOCAL

    @classmethod
    def set_network(cls, network: NetworkEnum):
        """
        Set the network to use when reading config values

        :param network: network to use when reading config values
        :type network: NetworkEnum
        """
        cls.__network = network
        if cls.__instance is not None:
            cls.__instance.set_network(network)

    @staticmethod
    def find_config_path() -> Path | None:
        """
        Find the config path to consider.
        Looks first for a config path in the env variables and then look
        if a local config file exists

        :return: Path of a found config file if it exists
        :rtype: Path | None
        """
        # first check if a config is specified by env var
        try:
            path = os.environ["MXOPS_CONFIG"]
        except KeyError:
            path = None

        if path is not None:
            if os.path.exists(path):
                return path
            raise ValueError("MXOPS_CONFIG env var does not direct to an existing path")

        # then check if a config file is present in the working directory
        path = Path("./mxops_config.ini")
        if os.path.exists(path):
            return path

        # no config found
        return None

    @classmethod
    def get_config(cls) -> _Config:
        """
        Create a _Config instance if it does not exists.

        :param config_path: path to the configuration file, defaults to './config.ini'
        :type config_path: Path, optional
        :return: _Config instance
        :rtype: _Config
        """
        if cls.__instance is None:
            config_path = cls.find_config_path()
            cls.__instance = _Config(cls.__network, config_path)
        return cls.__instance
