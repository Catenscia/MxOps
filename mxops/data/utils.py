"""
author: Etienne Wallet

This module contains some utils functions and classes
"""

import json
import base64
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from multiversx_sdk import Address, TokenTransfer
from multiversx_sdk.core.errors import BadAddressError, BadPubkeyLengthError


class CustomEncoder(json.JSONEncoder):
    """
    Custom Encoder for the MxOps package
    """

    def default(self, o: Any) -> Any:
        """
        Override the default function for the JSONEncoder to take into account
        bytes data

        :param o: object to encode
        :type o: Any
        :return: encoded object
        :rtype: Any
        """
        if isinstance(o, bytes):
            base64_encoded = base64.b64encode(o).decode("utf-8")
            return f"bytes:{base64_encoded}"
        if isinstance(o, SimpleNamespace):
            return o.__dict__.copy()
        # Let the base class default method raise the TypeError
        return json.JSONEncoder.default(self, o)


def decode_bytes(data: Any) -> Any:
    """
    If the data is detected to ba a custom encoded bytes, will decode it

    :param data: data to decode
    :type data: Any
    :return: decoded or raw data
    :rtype: Any
    """
    if isinstance(data, str) and data.startswith("bytes:"):
        base64_encoded = data[6:]  # Remove 'bytes:' prefix
        return base64.b64decode(base64_encoded)
    return data


def custom_decoder(item: Any) -> dict:
    """
    Custom decoded to use when calling json.load

    :param item: data to decode
    :type item: Any
    :return: decoded data
    :rtype: dict
    """
    if isinstance(item, dict):
        return {key: custom_decoder(value) for key, value in item.items()}
    if isinstance(item, list):
        return [custom_decoder(element) for element in item]
    if isinstance(item, str) and item.startswith("bytes:"):
        base64_encoded = item[6:]  # Remove 'bytes:' prefix
        return base64.b64decode(base64_encoded)
    return item


def json_dump(file_path: Path, obj: Any):
    """
    Small wrapper arount json.dump that uses the custom encoder

    :param path: path where to dump the data
    :type path: Path
    :param obj: obj to dump
    :type obj: Any
    """
    content = json_dumps(obj)
    file_path.write_text(content)


def json_dumps(obj: Any) -> str:
    """
    Small wrapper arount json.dumps that uses the custom encoder

    :param obj: obj to dump
    :type obj: Any
    :return: dumped data
    :rtype: str
    """
    return json.dumps(obj, cls=CustomEncoder, indent=4)


def json_load(file_path: Path) -> Any:
    """
    Small wrapper arount json.load that uses the custom decoder


    :param file_path: path of the data to load
    :type file_path: Path
    :return: loaded data
    :rtype: Any
    """
    with open(file_path.as_posix(), "r", encoding="utf-8") as file:
        return json.load(file, object_hook=custom_decoder)


def json_loads(obj_str: str) -> Any:
    """
    Small wrapper arount json.loads that uses the custom decoder


    :param obj_str: data to load
    :type obj_str: str
    :return: loaded data
    :rtype: Any
    """
    return json.loads(obj_str, object_hook=custom_decoder)


def convert_mx_data_to_vanilla(obj: Any) -> Any:
    """
    Convert data from the mx-sky-py package to vanilla python

    :param obj: object to convert
    :type obj: Any
    :return: converted object
    :rtype: Any
    """
    if isinstance(obj, bytes):
        try:
            return Address(obj).to_bech32()
        except (BadAddressError, BadPubkeyLengthError):
            return obj
    if isinstance(obj, TokenTransfer):
        return {
            "amount": obj.amount,
            "identifier": obj.token.identifier,
            "nonce": obj.token.nonce,
        }
    if isinstance(obj, SimpleNamespace):  # _EnumPayload
        return convert_mx_data_to_vanilla(obj.__dict__.copy())
    if isinstance(obj, dict):
        return {
            convert_mx_data_to_vanilla(k): convert_mx_data_to_vanilla(v)
            for k, v in obj.items()
        }
    if isinstance(obj, list):
        return list(convert_mx_data_to_vanilla(e) for e in obj)
    if isinstance(obj, set):
        return set(convert_mx_data_to_vanilla(e) for e in obj)
    if isinstance(obj, tuple):
        return tuple(convert_mx_data_to_vanilla(e) for e in obj)
    return obj
