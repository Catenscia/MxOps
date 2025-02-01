"""
This module contains the functions to create Checks
It is separated to avoid having circular import
"""

from dataclasses import dataclass
import importlib
from typing import Any
from mxops import errors
from mxops.execution.checks.base import Check
from mxops.execution.smart_values import SmartValue


@dataclass
class SmartCheck(SmartValue):
    """
    Represent a smart value that should result in a step
    """

    @staticmethod
    def type_enforce_value(value: Any) -> Check:
        """
        Convert a value to the expected evaluated type

        :param value: value to convert
        :type value: Any
        :return: converted value
        :rtype: Step
        """
        if isinstance(value, Check):
            return value
        if isinstance(value, dict):
            return instanciate_checks([value])[0]
        raise ValueError(f"Cannot create a check from type {type(value)} ({value})")

    def get_evaluated_value(self) -> Check:
        """
        Return the evaluated value

        :return: evaluated value
        :rtype: Check
        """
        return super().get_evaluated_value()


@dataclass
class SmartChecks(SmartValue):
    """
    Represent a smart value that should result in a list of steps
    """

    @staticmethod
    def type_enforce_value(value: Any) -> list[Check]:
        """
        Convert a value to the expected evaluated type

        :param value: value to convert
        :type value: Any
        :return: converted value
        :rtype: list[Check]
        """
        result = []
        for raw_step in list(value):
            step = SmartCheck(raw_step)
            step.evaluate()
            result.append(step.get_evaluated_value())
        return result

    def get_evaluated_value(self) -> list[Check]:
        """
        Return the evaluated value

        :return: evaluated value
        :rtype: list[Check]
        """
        return super().get_evaluated_value()


def instanciate_checks(raw_checks: list[dict]) -> list[Check]:
    """
    Take checks as dictionaries and convert them to their corresponding check classes.

    :param raw_checks: checks to instantiate
    :type raw_checks: list[dict]
    :return: checks instances
    :rtype: list[Check]
    """
    checks_list = []
    for raw_check in raw_checks:
        check_type = raw_check.pop("type")
        check_class_name = (
            check_type if check_type.endswith("Check") else check_type + "Check"
        )
        try:
            module = importlib.import_module("mxops.execution.checks")
            check_class_object = getattr(module, check_class_name)
        except (ImportError, AttributeError) as err:
            raise errors.UnkownStep(check_type) from err
        try:
            checks_list.append(check_class_object(**raw_check))
        except Exception as err:
            raise errors.InvalidCheckDefinition(check_type, raw_check) from err
    return checks_list
