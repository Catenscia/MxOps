"""
author: Etienne Wallet

This module contains abstract base Steps that are used to construct other Steps
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from types import UnionType
from typing import Type, get_args

from mxops.execution.smart_values import SmartValue


def extract_first_smart_value_class(field_type: Type | UnionType) -> Type | None:
    """
    Extract the first Smart Value type within a type field
    if none is found, return None

    :param field_type: field type to inspect
    :type field_type: Type | UnionType
    :return: extract type
    :rtype: Type | None
    """
    if isinstance(field_type, UnionType):
        possible_types = get_args(field_type)
        smart_value_type = next(
            (t for t in possible_types if issubclass(t, SmartValue)), None
        )
        if smart_value_type:
            return smart_value_type
    elif issubclass(field_type, SmartValue):
        return field_type
    return None


@dataclass
class Step(ABC):
    """
    Represents an instruction for MxOps to execute
    within a scene
    """

    def execute(self):
        """
        Function that manage the workflow of the execution of a step
        Currently, it only evaluate all the smart values before triggering
        the actual execution of the step
        """
        self.evaluate_smart_values()
        self._execute()

    @abstractmethod
    def _execute(self):
        """
        Interface for the method to execute the action described by a Step instance.
        Each child class must overrid this method
        """

    def _auto_convert_smart_values_attributes(self):
        """
        Automatically convert attributes that are expected to be smart values
        into their expected class
        """
        # pylint: disable=no-member
        for attr_name, attr in self.__dataclass_fields__.items():
            attr_value = getattr(self, attr_name)
            smart_type = extract_first_smart_value_class(attr.type)
            if attr_value is None or smart_type is None:
                continue
            if isinstance(attr_value, smart_type):
                continue
            if not issubclass(smart_type, SmartValue):
                continue
            setattr(self, attr_name, smart_type(attr_value))

    def __post_init__(self):
        """
        Trigger functions after instantiation of the class
        """
        self._auto_convert_smart_values_attributes()

    def evaluate_smart_values(self):
        """
        Trigger the evaluation method of all smart values fields
        """
        # pylint: disable=no-member
        for attr_name in self.__dataclass_fields__:
            attr_value = getattr(self, attr_name)
            if isinstance(attr_value, SmartValue):
                attr_value.evaluate()
