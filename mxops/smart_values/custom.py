"""
author: Etienne Wallet

This module contains smart values pointing to custom MxOps classes
"""

from dataclasses import dataclass
from typing import Any

from multiversx_sdk import Token
from mxops.execution.msc import OnChainTokenTransfer, ResultsSaveKeys
from mxops.smart_values.base import SmartValue
from mxops.smart_values.mx_sdk import SmartAddress
from mxops.smart_values.native import SmartInt, SmartStr


@dataclass
class SmartOnChainTokenTransfer(SmartValue):
    """
    Represent a smart value that should result in an OnChainTokenTransfer
    """

    @staticmethod
    def type_enforce_value(value: Any) -> OnChainTokenTransfer:
        """
        Convert a value to the expected evaluated type

        :param value: value to convert
        :type value: Any
        :return: converted value
        :rtype: OnChainTokenTransfer
        """
        if isinstance(value, OnChainTokenTransfer):
            return value
        if isinstance(value, list):
            if len(value) < 2:
                raise ValueError(
                    "OnChainTokenTransfer should have at least four elements: "
                    "sender, receiver, identifier and amount"
                )
            # assume sender, receiver, identifier, amount, nonce
            sender = value[0]
            receiver = value[1]
            token_identifier = value[2]
            amount = value[3]
            if len(value) >= 5:
                nonce = value[4]
            else:
                nonce = 0
        elif isinstance(value, dict):
            try:
                sender = value["sender"]
                receiver = value["receiver"]
                amount = value["amount"]
            except KeyError as err:
                raise ValueError("Missing kwarg for the OnChainTokenTransfer") from err
            try:
                token_identifier = value["identifier"]
            except KeyError:
                try:
                    token_identifier = value["token_identifier"]
                except KeyError as err:
                    raise ValueError(
                        "Missing identifier or token_identifier kwarg"
                        " for the token transfer"
                    ) from err
            try:
                nonce = value["nonce"]
            except KeyError:
                try:
                    nonce = value["token_nonce"]
                except KeyError:
                    nonce = 0

        else:
            raise ValueError(
                f"Cannot enforce type {type(value)} to TokenTransfer (value: {value})"
            )
        sender = SmartAddress(sender)
        sender.evaluate()
        receiver = SmartAddress(receiver)
        receiver.evaluate()
        token_identifier = SmartStr(token_identifier)
        token_identifier.evaluate()
        amount = SmartInt(amount)
        amount.evaluate()
        nonce = SmartInt(nonce)
        nonce.evaluate()
        return OnChainTokenTransfer(
            sender.get_evaluated_value(),
            receiver.get_evaluated_value(),
            Token(token_identifier.get_evaluated_value(), nonce.get_evaluated_value()),
            amount.get_evaluated_value(),
        )

    def get_evaluated_value(self) -> OnChainTokenTransfer:
        """
        Return the evaluated value and enforce a type if necessary

        :return: evaluated value
        :rtype: OnChainTokenTransfer
        """
        return super().get_evaluated_value()


@dataclass
class SmartOnChainTokenTransfers(SmartValue):
    """
    Represent a smart value that should result in a list of OnChainTokenTransfers
    """

    @staticmethod
    def type_enforce_value(value: Any) -> list[OnChainTokenTransfer]:
        """
        Convert a value to the expected evaluated type

        :param value: value to convert
        :type value: Any
        :return: converted value
        :rtype: list[OnChainTokenTransfer]
        """
        result = []
        for transfer in list(value):
            transfer = SmartOnChainTokenTransfer(transfer)
            transfer.evaluate()
            result.append(transfer.get_evaluated_value())
        return result

    def get_evaluated_value(self) -> list[OnChainTokenTransfer]:
        """
        Return the evaluated value and enforce a type if necessary

        :return: evaluated value
        :rtype: list[OnChainTokenTransfer]
        """
        return super().get_evaluated_value()


@dataclass
class SmartResultsSaveKeys(SmartValue):
    """
    Represent a smart value that should result in a ResultsSaveKeys
    """

    @staticmethod
    def type_enforce_value(value: Any) -> ResultsSaveKeys:
        """
        Convert a value to the expected evaluated type

        :param value: value to convert
        :type value: Any
        :return: converted value
        :rtype: ResultsSaveKeys
        """
        return ResultsSaveKeys.from_input(value)

    def get_evaluated_value(self) -> ResultsSaveKeys:
        """
        Return the evaluated value and enforce a type if necessary

        :return: evaluated value
        :rtype: ResultsSaveKeys
        """
        return super().get_evaluated_value()
