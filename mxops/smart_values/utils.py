"""
author: Etienne Wallet

This module contains utils functions for smart values
"""

import base64
import math
import os
import re
from typing import Any

from multiversx_sdk import Address, TokenTransfer
from multiversx_sdk.core.errors import BadAddressError
import numpy as np
from simpleeval import EvalWithCompoundTypes

from mxops import errors
from mxops.config.config import Config
from mxops.data.execution_data import ScenarioData


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
            "ceil": math.ceil,
            "len": len,
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
        retrieved_value = (
            f"{arg[:match_start]}{retrieved_value}{arg[closing_pos + 1 :]}"
        )
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


def get_address_instance(raw_address: str) -> Address:
    """
    From a string return an Address instance.
    The input will be parsed to dynamically evaluate values from the environment,
    the config, saved data or from the defined contracts or accounts.

    :param address_str: raw address or address entity designation
    :type address_str: str
    :return: address instance corresponding to the input
    :rtype: Address
    """
    if isinstance(raw_address, Address):
        return raw_address
    # try to see if the string is a valid address
    try:
        return Address.from_bech32(raw_address)
    except BadAddressError:
        pass

    # else try to see if it is a valid contract id or account name
    try:
        return ScenarioData.get().get_account_address(raw_address)
    except errors.UnknownAccount:
        pass

    raise errors.ParsingError(raw_address, "address_str address")


def force_str(value: Any) -> str:
    """
    for the use of str in an object instead of __repr__ when
    __repr__ is not defined

    :param value: valeu to convert to str
    :type value: Any
    :return: converted value
    :rtype: str
    """
    if isinstance(value, list):
        as_str = []
        for e in value:
            if isinstance(e, TokenTransfer):
                as_str.append(str(e))
            else:
                as_str.append(e)
        return str(as_str)
    return str(value)
