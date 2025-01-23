"""
author: Etienne Wallet

This module contains the classes and functions to describe smart values,
which are values evaluated at run time
"""

from dataclasses import dataclass, field
import os
import re
from typing import Any, List, Optional

from multiversx_sdk import Address
from multiversx_sdk.core.errors import BadAddressError

from mxops import errors
from mxops.config.config import Config
from mxops.data.execution_data import ScenarioData
from mxops.execution.account import AccountsManager


def convert_arg(arg: Any, desired_type: Optional[str]) -> Any:
    """
    Convert an argument to a desired type.
    Supported type are str and int

    :param arg: argument to convert
    :type arg: Any
    :param desired_type: type to convert the argument to
    :type desired_type: Optional[str]
    :return: converted argument if a specified type was provided
    :rtype: Any
    """
    if desired_type == "str":
        return str(arg)
    if desired_type == "int":
        return int(arg)
    return arg


def retrieve_value_from_string(arg: str) -> Any:
    """
    Check if a string argument contains an env var, a config var or a data var.
    If None of the previous apply, return the string unchanged
    Examples of formated strings:

    $MY_VAR:int
    &my-var:str
    %KEY_1.KEY_2[0].MY_VAR
    %{composed}_var
    %{%{parametric}_${VAR}}

    :param arg: argument to check
    :type arg: str
    :return: untouched argument or retrieved value
    :rtype: Any
    """
    if arg.startswith("0x"):
        return bytes.fromhex(arg[2:])
    pattern = r"(.*)([$&%])\{?([a-zA-Z0-9_\-\.\]\[]+):?([a-zA-Z]*)\}?(.*)"
    result = re.match(pattern, arg)
    if result is None:
        return arg
    pre_arg, symbol, inner_arg, desired_type, post_arg = result.groups()
    if symbol == "%":
        scenario_data = ScenarioData.get()
        retrieved_value = scenario_data.get_value(inner_arg)
    elif symbol == "&":
        config = Config.get_config()
        retrieved_value = config.get(inner_arg.upper())
    elif symbol == "$":
        retrieved_value = os.environ[inner_arg]
    else:
        raise errors.InvalidDataFormat(f"Unknow symbol {symbol}")
    retrieved_value = convert_arg(retrieved_value, desired_type)

    if pre_arg != "" or post_arg != "":
        retrieved_value = f"{pre_arg}{retrieved_value}{post_arg}"
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
            mid_val_str = str(mid_val)
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
        :rtype: int
        """
        return super().get_evaluated_value()
