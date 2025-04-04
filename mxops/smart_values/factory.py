"""
This module contains the functions to create SmartValues
It is separated to avoid having circular import
"""

import importlib
from types import UnionType
from typing import Type, Union, get_args, get_origin

from mxops.smart_values.base import SmartValue


MODULES_WITH_SMART_VALUES = [
    "mxops.smart_values",
    "mxops.execution.checks.factory",
    "mxops.execution.steps.factory",
]


def extract_smart_values_type_from_str(type_str: str) -> Type | None:
    """
    from a smart value name, return the associated classes by scanning all the modules
    that may contains such type

    :param type_str: type to retrieve
    :type type_str: str
    :return: retrieved type if it exists
    :rtype: Type | None
    """
    if "Smart" not in type_str:
        return None
    for module_name in MODULES_WITH_SMART_VALUES:
        try:
            module = importlib.import_module(module_name)
            return getattr(module, type_str)
        except (ImportError, AttributeError):
            continue
    return None


def parse_field_type_from_str(field_type_str: str) -> Type | UnionType | None:
    """
    convert a field type as a string to actual types

    :param field_type_str: file type as a string
    :type field_type_str: str
    :return: extracted type(s)
    :rtype: Type | UnionType | None
    """
    # Split the string by '|' for union types
    type_strings = [t.strip() for t in field_type_str.split("|")]

    actual_types = []
    for type_str in type_strings:
        if type_str == "None":
            actual_type = type(None)
        else:
            actual_type = extract_smart_values_type_from_str(type_str)
            if actual_type is None:
                continue
        actual_types.append(actual_type)

    if len(actual_types) > 1:
        return Union[tuple(actual_types)]
    if actual_types:
        return actual_types[0]
    return None


def extract_first_smart_value_class(
    field_type: Type | UnionType | str | None,
) -> Type | None:
    """
    Extract the first Smart Value type within a type field
    if none is found, return None

    :param field_type: field type to inspect
    :type field_type: Type | UnionType | str
    :return: extract type
    :rtype: Type | None
    """
    if field_type is None:
        return None
    if isinstance(field_type, str):
        field_type = parse_field_type_from_str(field_type)
        return extract_first_smart_value_class(field_type)
    if isinstance(field_type, UnionType) or get_origin(field_type) is Union:
        possible_types = get_args(field_type)
        for t in possible_types:
            if issubclass(t, SmartValue):
                return t
        return None
    if isinstance(field_type, type) and issubclass(field_type, SmartValue):
        return field_type
    return None
