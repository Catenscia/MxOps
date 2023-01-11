"""
author: Etienne Wallet

Various elements for the execution sub package
"""
from dataclasses import dataclass


@dataclass
class EsdtTransfer:
    """
    Represent any type of ESDT transfer (Simple ESDT, NFT, SFT, MetaESDT)
    """
    token_identifier: str
    amount: int
    nonce: int = 0
