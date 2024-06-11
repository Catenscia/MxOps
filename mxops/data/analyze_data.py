"""
author: Etienne Wallet

This module contains the functions to load, write and update transaction data
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict

from mxops.data.path import get_tx_file_path
from mxops.data.utils import json_dump, json_load
from mxops.utils.logger import get_logger

LOGGER = get_logger("analyze_data")


@dataclass
class TransactionsData:
    """
    This class represents the save format for the transactions of a contract
    """

    contract_beh32_address: str
    raw_transactions: Dict = field(default_factory=dict)  # transactions saved by hash
    transactions_offset: int = 0  # offset to fetch transactions used for the queries
    transactions_offset_origin: int = 0  # timestamp used as start time for the queries

    def save(self):
        """
        Save this scenario data where it belongs.
        Overwrite any existing file. Will save a checkpoint if provided

        :param checkpoint: contract id or token name that hosts the value
        :type checkpoint: str
        """
        file_path = get_tx_file_path(self.contract_beh32_address)
        json_dump(file_path, self.__dict__)

    def add_transactions(self, new_raw_transactions: Dict):
        """
        Add new transactions to the data

        :param new_raw_transactions: transactions to add
        :type new_raw_transactions: Dict
        """
        for raw_transaction in new_raw_transactions:
            try:
                tx_hash = raw_transaction["txHash"]
            except KeyError:
                LOGGER.warning(
                    f"Fetched raw transaction has no hash: {raw_transaction}"
                )
                continue
            self.raw_transactions[tx_hash] = raw_transaction

    @staticmethod
    def load_from_file(contract_beh32_address: str) -> TransactionsData:
        """
        Load the existing transaction data of a contract

        :param contract_beh32_address: address of the contract to load
        :type contract_beh32_address: str
        :return: loaded data
        :rtype: TransactionsData
        """
        file_path = get_tx_file_path(contract_beh32_address)
        raw_data = json_load(file_path)
        return TransactionsData(**raw_data)
