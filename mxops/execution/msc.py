"""
author: Etienne Wallet

Various elements for the execution sub package
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any

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


@dataclass
class ResultsSaveKeys:
    """
    Class describing how the results of a query or a call should be
    saved. Namely, under which key(s) save which result(s)
    """

    master_key: str | None
    sub_keys: list[str | None] | None

    @staticmethod
    def from_input(data: Any) -> ResultsSaveKeys | None:
        """
        Parse the user input as an instance of this class

        :param data: input data for a yaml Scene file
        :type data: Any
        :return: results save keys if defined
        :rtype: ResultsSaveKeys | None
        """
        if data is None:
            return None
        if isinstance(data, ResultsSaveKeys):
            return data
        if isinstance(data, str):
            return ResultsSaveKeys(data, None)
        if isinstance(data, list):
            for save_key in data:
                if not isinstance(save_key, str) and save_key is not None:
                    raise TypeError(f"Save keys must be a str or None, got {save_key}")
            return ResultsSaveKeys(None, data)
        if isinstance(data, dict):
            if len(data) != 1:
                raise ValueError(
                    "When providing a dict, only one root key should be provided"
                )
            master_key, sub_keys = list(data.items())[0]
            if not isinstance(master_key, str):
                raise TypeError("The root key should be a str")
            for save_key in sub_keys:
                if not isinstance(save_key, str) and save_key is not None:
                    raise TypeError(f"Save keys must be a str or None, got {save_key}")
            return ResultsSaveKeys(master_key, sub_keys)
        raise TypeError(f"ResultsSaveKeys can not parse the following input {data}")

    def parse_data_to_save(self, data: list) -> dict:
        """
        Parse data and break it into key-value pairs to save as data

        :param data: data to parse according the the results keys of this instance
        :type data: list
        :return: key-value pairs to save
        :rtype: dict
        """
        sub_keys = self.sub_keys
        if sub_keys is not None:
            if len(sub_keys) != len(data):
                raise ValueError(
                    f"Number of data parts ({len(data)} -> "
                    f"{data}) and save keys "
                    f"({len(sub_keys)} -> {sub_keys}) doesn't match"
                )
            to_save = dict(zip(sub_keys, data))
            if self.master_key is not None:
                to_save = {self.master_key: to_save}
        else:
            to_save = {self.master_key: data}
        return to_save
