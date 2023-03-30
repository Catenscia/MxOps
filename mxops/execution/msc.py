"""
author: Etienne Wallet

Various elements for the execution sub package
"""
from dataclasses import dataclass
from typing import Any


@dataclass
class EsdtTransfer:
    """
    Represent any type of ESDT transfer (Simple ESDT, NFT, SFT, MetaESDT)
    """
    token_identifier: str
    amount: int
    nonce: int = 0


@dataclass
class OnChainTransfer:
    """
    Represent any type of token transfer on chain
    """
    sender: str
    receiver: str
    token: str
    amount: str

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, ExpectedTransfer) or isinstance(other, OnChainTransfer):
            return (self.sender, self.receiver, self.token, self.amount) == (other.sender,
                                                                             other.receiver,
                                                                             other.token,
                                                                             other.amount)
        return False


@dataclass
class ExpectedTransfer:
    """
    Holds the information of a transfert that is expected to be found in an on-chain transaction
    """
    sender: str
    receiver: str
    token: str
    amount: str

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, ExpectedTransfer) or isinstance(other, OnChainTransfer):
            return (self.sender, self.receiver, self.token, self.amount) == (other.sender,
                                                                             other.receiver,
                                                                             other.token,
                                                                             other.amount)
        return False
