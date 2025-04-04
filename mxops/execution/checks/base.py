"""
author: Etienne Wallet

This module contains abstract base Checks that are used to construct other Checks
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass

from multiversx_sdk import TransactionOnNetwork

from mxops import errors
from mxops.smart_values import SmartValue
from mxops.smart_values.factory import extract_first_smart_value_class


@dataclass
class Check(ABC):
    """
    Represents a check to operate on the content of an on-chain transaction
    """

    def raise_on_failure(self, onchain_tx: TransactionOnNetwork):
        """
        Perform the check on the transaction and raise an error if it failed.

        :param onchain_tx: transaction to perform the check on
        :type onchain_tx: TransactionOnNetwork
        """
        try:
            check_status = self.get_check_status(onchain_tx)
        except Exception as err:
            raise errors.CheckFailed(self, onchain_tx) from err
        if not check_status:
            raise errors.CheckFailed(self, onchain_tx)

    def get_check_status(self, onchain_tx: TransactionOnNetwork) -> bool:
        """
        Evaluate the smart values of a check befor evaluating the status

        :param onchain_tx: transaction to perform the check on
        :type onchain_tx: TransactionOnNetwork
        :return: True if the check pass
        :rtype: bool
        """
        self.evaluate_smart_values()
        return self._get_check_status(onchain_tx)

    @abstractmethod
    def _get_check_status(self, onchain_tx: TransactionOnNetwork) -> bool:
        """
        Interface for the method to execute the check described by a Check instance.
        Each child class must overrid this method

        :param onchain_tx: transaction to perform the check on
        :type onchain_tx: TransactionOnNetwork
        :return: True if the check pass
        :rtype: bool
        """

    def _auto_convert_smart_values_attributes(self):
        """
        Automatically convert attributes that are expected to be smart values
        into their expected class
        """
        # pylint: disable=no-member
        for attr_name, attr in self.__dataclass_fields__.items():
            attr_value = getattr(self, attr_name)
            smart_type = extract_first_smart_value_class(attr.type)
            if attr_value is None or smart_type is None:
                continue
            if isinstance(attr_value, smart_type):
                continue
            if not issubclass(smart_type, SmartValue):
                continue
            setattr(self, attr_name, smart_type(attr_value))

    def __post_init__(self):
        """
        Trigger functions after instantiation of the class
        """
        self._auto_convert_smart_values_attributes()

    def evaluate_smart_values(self):
        """
        Trigger the evaluation method of all smart values fields
        """
        # pylint: disable=no-member
        for attr_name in self.__dataclass_fields__:
            attr_value = getattr(self, attr_name)
            if isinstance(attr_value, SmartValue):
                attr_value.evaluate()
