"""
author: Etienne Wallet

Enums used in the MxOps package
"""

from enum import Enum
from typing import Type


class NetworkEnum(Enum):
    """
    Enum describing the allowed values for the network
    """

    MAIN = "mainnet"
    DEV = "devnet"
    TEST = "testnet"
    LOCAL = "localnet"
    CHAIN_SIMULATOR = "chain-simulator"


class TokenTypeEnum(Enum):
    """
    Enum describing the different token types on MultiversX
    """

    FUNGIBLE = "fungible"
    NON_FUNGIBLE = "non fungible"
    SEMI_FUNGIBLE = "semi fungible"
    META = "meta"


class LogGroupEnum(Enum):
    """
    Define the different groups of logging
    Useful to define log level per group
    """

    GNL = "general"
    CONFIG = "configuration"
    EXEC = "execution"
    DATA = "data"
    MSC = "miscellanious"


def parse_enum(value: str, enum_class: Type[Enum]) -> Enum:
    """
    Try to match a string to the name or the value of an instance of an Enum class

    :param value: valut to match
    :type value: str
    :param enum_class: Enum class to look into for a match
    :type enum_class: Enum
    :return: Enum instance that matched
    :rtype: Enum
    """
    try:
        return getattr(enum_class, value)
    except AttributeError:
        pass
    try:
        return enum_class(value)
    except ValueError:
        pass
    raise ValueError(f"{value} can not be matched to a {enum_class}")


def parse_network_enum(network: str) -> NetworkEnum:
    """
    Try to match a string to the name or the value of an instance of a NetworkEnum

    :param network: string to match to an enum
    :type network: str
    :return: NetworkEnum corresponding to the input string
    :rtype: NetworkEnum
    """
    return parse_enum(network, NetworkEnum)


def parse_token_type_enum(token_type: str) -> TokenTypeEnum:
    """
    Try to match a string to the name or the value of an instance of a TokenTypeEnum

    :param network: string to match to an enum
    :type network: str
    :return: TokenTypeEnum corresponding to the input string
    :rtype: TokenTypeEnum
    """
    return parse_enum(token_type, TokenTypeEnum)
