"""
author: Etienne Wallet

This module contains smart values pointing to MultiversX python sdk classes
"""

from dataclasses import dataclass
from typing import Any
from multiversx_sdk import Address, Token, TokenTransfer

from mxops.smart_values.base import SmartValue
from mxops.smart_values.native import SmartInt, SmartStr
from mxops.smart_values.utils import get_address_instance


@dataclass
class SmartAddress(SmartValue):
    """
    Represent a smart value that should result in an Address
    """

    @staticmethod
    def type_enforce_value(value: Any) -> Address:
        """
        Convert a value to the expected evaluated type

        :param value: value to convert
        :type value: Any
        :return: converted value
        :rtype: Address
        """
        return get_address_instance(value)

    def get_evaluated_value(self) -> Address:
        """
        Return the evaluated value and enforce a type if necessary

        :return: evaluated value
        :rtype: Address
        """
        return super().get_evaluated_value()


@dataclass
class SmartAddresses(SmartValue):
    """
    Represent a smart value that should result in a list of Addresses
    """

    @staticmethod
    def type_enforce_value(value: Any) -> list[Address]:
        """
        Convert a value to the expected evaluated type

        :param value: value to convert
        :type value: Any
        :return: converted value
        :rtype: list[Address]
        """
        return [get_address_instance(v) for v in value]

    def get_evaluated_value(self) -> list[Address]:
        """
        Return the evaluated value and enforce a type if necessary

        :return: evaluated value
        :rtype: list[Address]
        """
        return super().get_evaluated_value()


@dataclass
class SmartBech32(SmartValue):
    """
    Represent a smart value that should result in a bech32
    """

    @staticmethod
    def type_enforce_value(value: Any) -> str:
        """
        Convert a value to the expected evaluated type

        :param value: value to convert
        :type value: Any
        :return: converted value
        :rtype: str
        """
        return get_address_instance(value).to_bech32()

    def get_evaluated_value(self) -> str:
        """
        Return the evaluated value and enforce a type if necessary

        :return: evaluated value
        :rtype: str
        """
        return super().get_evaluated_value()


@dataclass
class SmartTokenTransfer(SmartValue):
    """
    Represent a smart value that should result in a TokenTransfer
    """

    @staticmethod
    def type_enforce_value(value: Any) -> TokenTransfer:
        """
        Convert a value to the expected evaluated type

        :param value: value to convert
        :type value: Any
        :return: converted value
        :rtype: TokenTransfer
        """
        if isinstance(value, TokenTransfer):
            return value
        if isinstance(value, list):
            if len(value) < 2:
                raise ValueError(
                    "Token transfer should have at least two elements: "
                    "identifier and amount"
                )
            # assume token identifier, amount, nonce
            token_identifier = value[0]
            amount = value[1]
            if len(value) >= 3:
                nonce = value[2]
            else:
                nonce = 0
        elif isinstance(value, dict):
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
            try:
                amount = value["amount"]
            except KeyError as err:
                raise ValueError("Missing amount kwarg for the token transfer") from err
        else:
            raise ValueError(
                f"Cannot enforce type {type(value)} to TokenTransfer (value: {value})"
            )

        token_identifier = SmartStr(token_identifier)
        token_identifier.evaluate()
        amount = SmartInt(amount)
        amount.evaluate()
        nonce = SmartInt(nonce)
        nonce.evaluate()
        return TokenTransfer(
            Token(token_identifier.get_evaluated_value(), nonce.get_evaluated_value()),
            amount.get_evaluated_value(),
        )

    def get_evaluated_value(self) -> TokenTransfer:
        """
        Return the evaluated value and enforce a type if necessary

        :return: evaluated value
        :rtype: TokenTransfer
        """
        return super().get_evaluated_value()


@dataclass
class SmartTokenTransfers(SmartValue):
    """
    Represent a smart value that should result in a list of TokenTransfers
    """

    @staticmethod
    def type_enforce_value(value: Any) -> list[TokenTransfer]:
        """
        Convert a value to the expected evaluated type

        :param value: value to convert
        :type value: Any
        :return: converted value
        :rtype: list[TokenTransfer]
        """
        result = []
        for transfer in list(value):
            transfer = SmartTokenTransfer(transfer)
            transfer.evaluate()
            result.append(transfer.get_evaluated_value())
        return result

    def get_evaluated_value(self) -> list[TokenTransfer]:
        """
        Return the evaluated value and enforce a type if necessary

        :return: evaluated value
        :rtype: list[TokenTransfer]
        """
        return super().get_evaluated_value()


@dataclass
class SmartToken(SmartValue):
    """
    Represent a smart value that should result in a Token
    """

    @staticmethod
    def type_enforce_value(value: Any) -> Token:
        """
        Convert a value to the expected evaluated type

        :param value: value to convert
        :type value: Any
        :return: converted value
        :rtype: Token
        """
        if isinstance(value, Token):
            return value
        if isinstance(value, list):
            if len(value) < 1:
                raise ValueError("Token should have at least the token identifier ")
            # assume token identifier and optionnaly nonce
            token_identifier = value[0]
            if len(value) >= 2:
                nonce = value[1]
            else:
                nonce = 0
        elif isinstance(value, dict):
            try:
                token_identifier = value["identifier"]
            except KeyError:
                try:
                    token_identifier = value["token_identifier"]
                except KeyError as err:
                    raise ValueError(
                        "Missing identifier or token_identifier kwarg for the token"
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
                f"Cannot enforce type {type(value)} to Token (value: {value})"
            )

        token_identifier = SmartStr(token_identifier)
        token_identifier.evaluate()
        nonce = SmartInt(nonce)
        nonce.evaluate()
        return Token(
            token_identifier.get_evaluated_value(), nonce.get_evaluated_value()
        )

    def get_evaluated_value(self) -> Token:
        """
        Return the evaluated value

        :return: evaluated value
        :rtype: Token
        """
        return super().get_evaluated_value()
