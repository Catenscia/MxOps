"""
author: Etienne Wallet

Various elements for the execution sub package
"""

from dataclasses import dataclass

from mxops.execution.smart_values import SmartAddress, SmartInt, SmartToken


@dataclass
class OnChainTokenTransfer:
    """
    Holds the information of an onchain token transfer
    """

    sender: SmartAddress
    receiver: SmartAddress
    token: SmartToken
    amount: SmartInt
