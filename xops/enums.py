"""
author: Etienne Wallet

Entry point for the xOps package.
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
