"""
author: Etienne Wallet

Various elements for the execution sub package
"""

from dataclasses import dataclass

from multiversx_sdk import Address, Token


@dataclass
class OnChainTokenTransfer:
    """
    Holds the information of an onchain token transfer
    """

    sender: Address
    receiver: Address
    token: Token
    amount: int
