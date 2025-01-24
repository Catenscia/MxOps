"""
author: Etienne Wallet

This module contains the classes and functions to describe smart values,
which are values evaluated at run time
"""

import base64
from dataclasses import dataclass, field
import os
import re
from typing import Any, List, Optional

from multiversx_sdk import Address, Token, TokenTransfer
from multiversx_sdk.core.errors import BadAddressError
import numpy as np
from simpleeval import EvalWithCompoundTypes

from mxops import errors
from mxops.config.config import Config
from mxops.data.execution_data import ScenarioData
from mxops.execution.account import AccountsManager


def replace_escaped_characters(s: str) -> str:
    """
    Replace the escape character on symbols used by MxOps
    ex: "45 \\% 5" -> r"42 % 5"

    :param s: string to modify
    :type s: str
    :return: modified string
    :rtype: s
    """
    escaped_characters = ["%", "&", "$", "=", "{", "}"]
    for char in escaped_characters:
        s = re.sub(rf"\\{char}", char, s)
    return s


def evaluate_formula(formula_str: str) -> Any:
    """
    evaluate the formula provided as a string by the user.
    Remove first the escape characters on MxOps symbols

    :param formula_str: formula to evaluate
    :type formula_str: str
    :return: result of the formula
    :rtype: Any
    """
    formula_str = replace_escaped_characters(formula_str)
    return EvalWithCompoundTypes(
        functions={
            "int": int,
            "str": str,
            "float": float,
            "rand": np.random.rand,
            "randint": np.random.randint,
            "choice": np.random.choice,
        }
    ).eval(formula_str)


def force_bracket(s: str) -> str:
    """
    Add brackets if the string is using a single
    direct MxOps symbols

    :param s: string to modify
    :type s: str
    :return: modified string
    :rtype: str
    """
    pattern = r"^([$&%=])([^\{].*)$"
    result = re.match(pattern, s)
    if result is not None:
        symbol, left_over = result.groups()
        s = f"{symbol}{{{left_over}}}"
    return s


def get_closing_char_position(string: str, closing_char: str) -> int:
    """
    Find the closing character matching the first character of the string
    characters can be escaped with backslashes

    :param string: string
    :type string: str
    :param closing_char: closing character ex: "}"
    :type closing_char: str
    :return: position of the closing character
    :rtype: int
    """
    opening_char = string[0]
    opening_counter = 0
    i = 0
    string_len = len(string)
    while i < string_len:
        c = string[i]
        if i > 0 and string[i - 1] == "\\":
            i += 1
            continue
        if c == opening_char:
            opening_counter += 1
        elif c == closing_char:
            opening_counter -= 1
        if opening_counter == 0:
            return i
        i += 1
    raise errors.ClosingCharNotFound(string, closing_char)


def retrieve_value_from_string(arg: str) -> Any:
    """
    Check if a string argument contains an env var, a config var or a data var,
    or a formula.
    If None of the previous apply, return the string unchanged
    Examples of formated strings:

    $MY_VAR
    &my-var
    %KEY_1.KEY_2[0].MY_VAR
    %{composed}_var
    %{%{parametric}_${VAR}}
    ={1 + 2 + 3}

    :param arg: argument to check
    :type arg: str
    :return: untouched argument or retrieved value
    :rtype: Any
    """
    if arg.startswith("bytes:"):
        base64_encoded = arg[6:]
        return base64.b64decode(base64_encoded)
    if arg.startswith("0x"):
        return bytes.fromhex(arg[2:])
    arg = force_bracket(arg)
    matches = list(re.finditer("[$&%=]\\{", arg))
    if len(matches) == 0:
        return arg
    match = matches[-1]  # start with the last one for correct resolution order
    match_start = match.start()
    match_end = match.end()
    symbol = arg[match_start]
    closing_pos = match_end - 1 + get_closing_char_position(arg[match_end - 1 :], "}")
    inner_arg = arg[match_end:closing_pos]

    if symbol == "%":
        scenario_data = ScenarioData.get()
        retrieved_value = scenario_data.get_value(inner_arg)
    elif symbol == "&":
        config = Config.get_config()
        retrieved_value = config.get(inner_arg.upper())
    elif symbol == "$":
        retrieved_value = os.environ[inner_arg]
    elif symbol == "=":
        retrieved_value = evaluate_formula(inner_arg)
    else:
        raise errors.InvalidDataFormat(f"Unknow symbol {symbol}")

    # reconstruct the string if needed
    if match_start > 0 or closing_pos < len(arg) - 1:
        retrieved_value = f"{arg[:match_start]}{retrieved_value}{arg[closing_pos + 1:]}"
    return retrieved_value


def retrieve_value_from_any(arg: Any) -> Any:
    """
    Dynamically evaluate the provided argument depending on its type.
    Otherwise it will be returned itself

    :param arg: argument to evaluate
    :type arg: Any
    :return: evaluated argument
    :rtype: Any
    """
    if isinstance(arg, str):
        return retrieve_value_from_string(arg)
    if isinstance(arg, list):
        return [retrieve_value_from_any(e) for e in arg]
    if isinstance(arg, dict):
        return {
            retrieve_value_from_any(k): retrieve_value_from_any(v)
            for k, v in arg.items()
        }
    return arg


def get_address_instance(address_str: str) -> Address:
    """
    From a string return an Address instance.
    The input will be parsed to dynamically evaluate values from the environment,
    the config, saved data or from the defined contracts or accounts.

    :param address_str: raw address or address entity designation
    :type address_str: str
    :return: address instance corresponding to the input
    :rtype: Address
    """
    # try to see if the string is a valid address
    try:
        return Address.from_bech32(address_str)
    except BadAddressError:
        pass

    # else try to see if it is a valid contract id
    try:
        evaluated_address_str = retrieve_value_from_string(f"%{address_str}.address")
        return Address.from_bech32(evaluated_address_str)
    except (BadAddressError, errors.WrongDataKeyPath):
        pass

    # finally try to see if it designates a defined account
    try:
        account = AccountsManager.get_account(evaluated_address_str)
        return account.address
    except errors.UnknownAccount:
        pass
    raise errors.ParsingError(address_str, "address_str address")


@dataclass
class SmartValue:
    """
    Represent a smart value that can have any type
    """

    raw_value: Any
    evaluated_values: Optional[List] = field(init=False, default=None)

    @property
    def is_evaluated(self) -> bool:
        """
        If the smart value has been evaluated

        :return: true if evaluated
        :rtype: bool
        """
        return self.evaluated_values is not None

    def require_evaluated(self):
        """
        Raise an error if the value has not been evaluated
        """
        if not self.is_evaluated:
            raise errors.SmartValueNotEvaluated

    def get_evaluation_string(self):
        """
        construct the string the show the different values that the raw_value
        has beed evaluated to.
        Ex "USDT-123456 (%{%{Bob-token}.identifier} -> %usdt.identifier)"
        """
        self.require_evaluated()
        evaluated_value = self.get_evaluated_value()
        evaluation_str = str(evaluated_value)
        middle_values_str = []
        previous_str = None
        for mid_val in [self.raw_value, *self.evaluated_values]:
            mid_val_str = replace_escaped_characters(str(mid_val))
            if mid_val_str in (evaluation_str, previous_str):
                continue
            previous_str = mid_val_str
            middle_values_str.append(mid_val_str)
        if len(middle_values_str) > 0:
            values_str = " -> ".join(s for s in middle_values_str)
            evaluation_str += f" ({values_str})"
        return evaluation_str

    def evaluate(self):
        """
        Evaluate the raw value and save the intermediary values until the
        final value is reached
        """
        k = 0
        self.evaluated_values = []
        last_value = None
        result = self.raw_value
        while result != last_value:
            last_value = result
            result = retrieve_value_from_any(last_value)
            self.evaluated_values.append(result)
            k += 1
            if k > 1000:
                raise errors.MaxIterationError(
                    f"Unable to evaluated raw value {self.raw_value}"
                )
        enforced_type_value = self.type_enforce_value(last_value)
        if (
            type(enforced_type_value) != type(last_value)
            or enforced_type_value != last_value
        ):
            self.evaluated_values.append(enforced_type_value)

    @staticmethod
    def type_enforce_value(value: Any) -> Any:
        """
        Convert a value to the expected evaluated type

        :param value: value to convert
        :type value: Any
        :return: converted value
        :rtype: Any
        """
        return value

    def get_evaluated_value(self) -> Any:
        """
        Return the evaluated value

        :return: evaluated value
        :rtype: Any
        """
        self.require_evaluated()
        return self.evaluated_values[-1]


@dataclass
class SmartInt(SmartValue):
    """
    Represent a smart value that should result in an int
    """

    @staticmethod
    def type_enforce_value(value: Any) -> int:
        """
        Convert a value to the expected evaluated type

        :param value: value to convert
        :type value: Any
        :return: converted value
        :rtype: int
        """
        return int(value)

    def get_evaluated_value(self) -> int:
        """
        Return the evaluated value

        :return: evaluated value
        :rtype: int
        """
        return super().get_evaluated_value()


@dataclass
class SmartBool(SmartValue):
    """
    Represent a smart value that should result in a boolean
    """

    @staticmethod
    def type_enforce_value(value: Any) -> bool:
        """
        Convert a value to the expected evaluated type

        :param value: value to convert
        :type value: Any
        :return: converted value
        :rtype: bool
        """
        return bool(value)

    def get_evaluated_value(self) -> bool:
        """
        Return the evaluated value

        :return: evaluated value
        :rtype: int
        """
        return super().get_evaluated_value()


@dataclass
class SmartStr(SmartValue):
    """
    Represent a smart value that should result in a string
    """

    @staticmethod
    def type_enforce_value(value: Any) -> str:
        """
        Convert a value to the expected evaluated type

        :param value: value to convert
        :type value: Any
        :return: converted value
        :rtype: bool
        """
        return str(value)

    def get_evaluated_value(self) -> str:
        """
        Return the evaluated value

        :return: evaluated value
        :rtype: int
        """
        return super().get_evaluated_value()


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
            if len(value) == 3:
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
