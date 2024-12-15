"""
author: Etienne Wallet

This module contains some utilities functions for the execution sub package
"""

import os
import re
from typing import Any, List, Optional

from multiversx_sdk_cli.contracts import QueryResult, SmartContract
from multiversx_sdk_core.address import Address
from multiversx_sdk_core.errors import ErrBadAddress

from mxops.config.config import Config
from mxops.data.execution_data import ScenarioData
from mxops import errors
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
    return retrieve_value_from_any(retrieved_value)


def retrieve_values_from_strings(args: List[str]) -> List[Any]:
    """
    Dynamically evaluate the value of each element of the provided list

    :param args: args to evaluate
    :type args: List[str]
    :return: evaluated arguments
    :rtype: List[Any]
    """
    return [retrieve_value_from_string(arg) for arg in args]


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


def format_tx_arguments(arguments: List[Any]) -> List[Any]:
    """
    Transform the arguments so they can be recognised by multiversx sdk core

    :param arguments: list of arguments to be supplied to a endpoint
    :type arguments: List[Any]
    :return: formatted arguments
    :rtype: List[Any]
    """
    formated_arguments = []
    for arg in arguments:
        # convert a first time as int arg can be entered as string
        if isinstance(arg, str):
            arg = retrieve_value_from_string(arg)
        formated_arg = arg
        if isinstance(arg, str):
            if arg.startswith("erd") and len(arg) == 62:
                formated_arg = Address.from_bech32(arg)
        formated_arguments.append(formated_arg)
    return formated_arguments


def retrieve_and_format_arguments(arguments: List[Any]) -> List[Any]:
    """
    Retrieve the MxOps value of the arguments if necessary and transform them
    to match multiversx sdk core format

    :param arguments: lisf of arguments to be supplied
    :type arguments: List[Any]
    :return: format args
    :rtype: List[Any]
    """
    return format_tx_arguments(retrieve_value_from_any(arguments))


def get_contract_instance(contract_str: str) -> SmartContract:
    """
    From a string return a smart contract instance.
    The input will be parsed to dynamically evaluate values from
    the environment, the config or from the saved data.

    :param contract_str: contract address or mxops value
    :type contract_str: str
    :return: smart contract corresponding to the address
    :rtype: SmartContract
    """
    # try to see if the string is a valid address
    try:
        return SmartContract(Address.from_bech32(contract_str))
    except ErrBadAddress:
        pass
    # otherwise try to parse it as a mxops value
    contract_address = retrieve_value_from_string(contract_str)
    try:
        return SmartContract(Address.from_bech32(contract_address))
    except ErrBadAddress:
        pass
    # lastly try to see if it is a valid contract id
    contract_address = retrieve_value_from_string(f"%{contract_str}.address")
    try:
        return SmartContract(Address.from_bech32(contract_address))
    except ErrBadAddress:
        pass
    raise errors.ParsingError(contract_str, "contract address")


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
    # try to parse it as a mxops value
    evaluated_address_str = retrieve_value_from_string(address_str)

    # try to see if the string is a valid address
    try:
        return Address.from_bech32(evaluated_address_str)
    except ErrBadAddress:
        pass

    # else try to see if it is a valid contract id
    try:
        evaluated_address_str = retrieve_value_from_string(f"%{address_str}.address")
        return Address.from_bech32(evaluated_address_str)
    except (ErrBadAddress, errors.WrongDataKeyPath):
        pass

    # finally try to see if it designates a defined account
    try:
        account = AccountsManager.get_account(evaluated_address_str)
        return account.address
    except errors.UnknownAccount:
        pass
    raise errors.ParsingError(address_str, "address_str address")


def parse_query_result(result: QueryResult, expected_return: str) -> Any:
    """
    Take the return of a query and tries to parse it in the specified return type

    :param result: result of a query
    :type result: QueryResult
    :param expected_return: expected return of the query
    :type expected_return: str
    :return: parsed result of the query
    :rtype: Any
    """
    if expected_return in ("number", "int"):
        return result.number
    if expected_return == "str":
        return bytes.fromhex(result.hex).decode()
    raise ValueError(f"Unkown expected return: {expected_return}")
