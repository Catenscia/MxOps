"""
author: Etienne Wallet

Enums used in the MxOps package
"""

from enum import Enum


class NetworkEnum(Enum):
    """
    Enum describing the allowed values for the network
    """
    MAIN = 'MAIN'
    DEV = 'DEV'
    TEST = 'TEST'
    LOCAL = 'LOCAL'
