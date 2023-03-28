"""
author: Etienne Wallet

Enums used in the MxOps package
"""

from enum import Enum


class NetworkEnum(Enum):
    """
    Enum describing the allowed values for the network
    """
    MAIN = 'mainnet'
    DEV = 'devnet'
    TEST = 'testnet'
    LOCAL = 'localnet'


def parse_network_enum(network: str) -> NetworkEnum:
    """
    Try to match a string the the name of the value of a NetworkEnum.

    :param network: string to match to an enum
    :type network: str
    :return: NetworkEnum corresponding to the input string
    :rtype: NetworkEnum
    """
    try:
        return getattr(NetworkEnum, network)
    except AttributeError:
        pass
    try:
        return NetworkEnum(network)
    except ValueError:
        pass
    raise ValueError(f'{network} can not be matched to a NetworkEnum')
