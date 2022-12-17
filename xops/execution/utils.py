"""
author: Etienne Wallet

This module contains some utilities functions for the execution sub package
"""
import os
from typing import Any, List, Optional, Tuple

from erdpy.accounts import Address

from xops.config.config import Config
from xops.data.data import _ScenarioData
from xops.errors import WrongScenarioDataReference


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
    try:
        return arg.split(':')
    except ValueError:
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
    elif desired_type == 'int':
        return int(arg)
    return arg


def retrieve_value_from_env(arg: str) -> str:
    """
    retrieve the value of an argument from the environment variables

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
    retrieve the value of an argument from the config

    :param arg: name of the variable prefixed with the & sign
    :type arg: str
    :return: value saved in the config
    :rtype: str
    """
    if not arg.startswith('&'):
        raise ValueError(f'the argument as no & sign: {arg}')
    inner_arg, desired_type = retrieve_specified_type(arg)
    config = Config.get()
    retrieved_value = config.get(inner_arg[1:].upper())
    return convert_arg(retrieved_value, desired_type)


def retrieve_value_from_scenario_data(scenario_data: _ScenarioData, arg: str) -> str:
    """
    Retrieve the value of an argument from scenario data.
    the argument must formated like this: %<contract_id>%<attribute>

    :param arg: name of the variable formated as above
    :type arg: str
    :param scenario_data: data of the current scenario
    :type scenario_data: ScenarioData
    :return: value saved in the config
    :rtype: str
    """
    inner_arg, desired_type = retrieve_specified_type(arg)
    try:
        contract_id, value_key = inner_arg[1:].split('%')
    except Exception as err:
        raise WrongScenarioDataReference from err
    retrieved_value = scenario_data.get_contract_value(contract_id, value_key)
    return convert_arg(retrieved_value, desired_type)


def retrieve_value_from_string(arg: str, scenario_data: _ScenarioData) -> Any:
    """
    Check if a string argument is intended to be an env var, a config var or a data var.
    If Nonce of the previous apply, return the string unchanged

    :param arg: argument to check
    :type arg: str
    :param scenario_data: data of the current scenario
    :type scenario_data: ScenarioData
    :return: untouched argument or retrieved value
    :rtype: Any
    """
    if arg.startswith('$'):
        return retrieve_value_from_env(arg)
    elif arg.startswith('&'):
        return retrieve_value_from_config(arg)
    elif arg.startswith('%'):
        return retrieve_value_from_scenario_data(scenario_data, arg)
    return arg


def format_tx_arguments(arguments: List[Any]) -> List[Any]:
    """
    Transform the arguments so they can be recognised by erdpy

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