"""
author: Etienne Wallet

This module contains some utilities functions for the execution sub package
"""
import os
from typing import Any, List, Optional, Tuple

from multiversx_sdk_cli.accounts import Address
from multiversx_sdk_cli.contracts import QueryResult

from mxops.config.config import Config
from mxops.data.data import ScenarioData
from mxops.errors import WrongScenarioDataReference
from mxops.execution.account import AccountsManager


def retrieve_specified_type(arg: str) -> Tuple[str, Optional[str]]:
    """
    Retrieve the type specified with the argument.
    Example:
        $MY_VAR:int
        &MY_VAR:str
        %CONTRACT%ID%MY_VAR:int

    :param arg: string arg passed
    :type arg: str
    :return: inner arg and name of the desired type if it exists
    :rtype: Tuple[str, Optional[str]]
    """
    if ':' in arg:
        return arg.split(':')
    return arg, None


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
    if desired_type == 'str':
        return str(arg)
    if desired_type == 'int':
        return int(arg)
    return arg


def retrieve_value_from_env(arg: str) -> str:
    """
    Retrieve the value of an argument from the environment variables

    :param arg: name of the variable prefixed with the $ sign
    :type arg: str
    :return: value saved in the environment
    :rtype: str
    """
    if not arg.startswith('$'):
        raise ValueError(f'the argument as no $ sign: {arg}')
    inner_arg, desired_type = retrieve_specified_type(arg)
    retrieved_value = os.environ[inner_arg[1:]]
    return convert_arg(retrieved_value, desired_type)


def retrieve_value_from_config(arg: str) -> str:
    """
    Retrieve the value of an argument from the config

    :param arg: name of the variable prefixed with the & sign
    :type arg: str
    :return: value saved in the config
    :rtype: str
    """
    if not arg.startswith('&'):
        raise ValueError(f'the argument as no & sign: {arg}')
    inner_arg, desired_type = retrieve_specified_type(arg)
    config = Config.get_config()
    retrieved_value = config.get(inner_arg[1:].upper())
    return convert_arg(retrieved_value, desired_type)


def retrieve_value_from_scenario_data(arg: str) -> str:
    """
    Retrieve the value of an argument from scenario data.
    the argument must formated like this: %<contract_id>%<attribute>

    :param arg: name of the variable formated as above
    :type arg: str
    :return: value saved in the config
    :rtype: str
    """
    inner_arg, desired_type = retrieve_specified_type(arg)
    try:
        contract_id, value_key = inner_arg[1:].split('%')
    except Exception as err:
        raise WrongScenarioDataReference from err

    scenario_data = ScenarioData.get()
    retrieved_value = scenario_data.get_contract_value(contract_id, value_key)
    return convert_arg(retrieved_value, desired_type)


def retrieve_address_from_account(arg: str) -> str:
    """
    Retrieve an address from the accounts manager.
    the argument must formated like this: [user]

    :param arg: name of the variable formated as above
    :type arg: str
    :return: address from the scenario
    :rtype: str
    """
    try:
        arg = arg[1:-1]
    except Exception as err:
        raise WrongScenarioDataReference from err

    account = AccountsManager.get_account(arg)
    return account.address.bech32()


def retrieve_value_from_string(arg: str) -> Any:
    """
    Check if a string argument is intended to be an env var, a config var or a data var.
    If Nonce of the previous apply, return the string unchanged

    :param arg: argument to check
    :type arg: str
    :return: untouched argument or retrieved value
    :rtype: Any
    """
    if arg.startswith('['):
        return retrieve_address_from_account(arg)
    if arg.startswith('$'):
        return retrieve_value_from_env(arg)
    if arg.startswith('&'):
        return retrieve_value_from_config(arg)
    if arg.startswith('%'):
        return retrieve_value_from_scenario_data(arg)
    return arg


def format_tx_arguments(arguments: List[Any]) -> List[Any]:
    """
    Transform the arguments so they can be recognised by mxpy

    :param arguments: list of arguments to be supplied to a endpoint
    :type arguments: List[Any]
    :return: formatted arguments
    :rtype: List[Any]
    """
    formated_arguments = []
    for arg in arguments:
        if isinstance(arg, str):  # done a first time as int arg can be entered as string
            arg = retrieve_value_from_string(arg)
        formated_arg = arg
        if isinstance(arg, str):
            if arg.startswith('erd') and len(arg) == 62:
                formated_arg = '0x' + Address(arg).hex()
            elif not arg.startswith('0x'):
                formated_arg = 'str:' + arg
        elif isinstance(arg, Address):
            formated_arg = '0x' + arg.hex()

        formated_arguments.append(formated_arg)
    return formated_arguments


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
    if expected_return == 'number':
        return result.number
    if expected_return == 'str':
        return bytes.fromhex(result.hex).decode()
    raise ValueError(f'Unkown expected return: {expected_return}')
