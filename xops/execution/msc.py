"""
author: Etienne Wallet

Various elements for the execution sub package
"""
from dataclasses import dataclass


@dataclass
class EsdtTransfer:
    token_identifier: str
    amount: int
    nonce: int = 0
