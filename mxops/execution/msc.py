"""
author: Etienne Wallet

Various elements for the execution sub package
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Union

from mxops.execution import utils


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
        if isinstance(other, ExpectedTransfer):
            return other == self
        if isinstance(other, OnChainTransfer):
            return (self.sender, self.receiver, self.token, self.amount) == (other.sender,
                                                                             other.receiver,
                                                                             other.token,
                                                                             other.amount)
        raise NotImplementedError


@dataclass
class ExpectedTransfer:
    """
    Holds the information of a transfert that is expected to be found in an on-chain transaction
    """
    sender: str
    receiver: str
    token: str
    amount: Union[int, str]

    def get_dynamic_evaluated(self) -> ExpectedTransfer:
        """
        Evaluate the attribute of the instance dynamically and return the corresponding expected
        transfer

        :return: instance dynamically evaluated
        :rtype: ExpectedTransfer
        """
        evaluations = {}
        attributes_to_extract = ['sender', 'receiver', 'token', 'amount']
        for attribute_name in attributes_to_extract:
            extracted_value = utils.retrieve_value_from_string(str(getattr(self, attribute_name)))
            evaluations[attribute_name] = extracted_value
        return ExpectedTransfer(**evaluations)

    def __eq__(self, other: Any) -> bool:
        evaluated_self = self.get_dynamic_evaluated()
        if isinstance(other, OnChainTransfer):
            evaluated_other = other
        elif isinstance(other, ExpectedTransfer):
            evaluated_other = other.get_dynamic_evaluated()
        else:
            raise NotImplementedError
        return (
            evaluated_self.sender,
            evaluated_self.receiver,
            evaluated_self.token,
            str(evaluated_self.amount)) == (evaluated_other.sender,
                                            evaluated_other.receiver,
                                            evaluated_other.token,
                                            str(evaluated_other.amount))
