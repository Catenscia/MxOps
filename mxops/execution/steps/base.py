"""
author: Etienne Wallet

This module contains abstract base Steps that are used to construct other Steps
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass

from mxops.execution.smart_values import SmartValue


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
        for attr_name in self.__dataclass_fields__:
            attr_value = getattr(self, attr_name)
            field_type = self.__dataclass_fields__[attr_name].type
            if isinstance(attr_value, field_type):
                continue
            if not issubclass(field_type, SmartValue):
                continue
            setattr(self, attr_name, field_type(attr_value))

    def __post_init__(self):
        """
        Trigger functions after instantiation of the class
        """
        self._auto_convert_smart_values_attributes()

    def evaluate_smart_values(self):
        """
        Trigger the evaluation method of all smart values fields
        """
        for attr_name in self.__dataclass_fields__:
            attr_value = getattr(self, attr_name)
            if isinstance(attr_value, SmartValue):
                attr_value.evaluate()
