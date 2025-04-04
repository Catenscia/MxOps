"""
This module contains the functions to create Checks
It is separated to avoid having circular import
"""

from copy import deepcopy
from dataclasses import dataclass
import importlib
from typing import Any
from mxops import errors
from mxops.execution.checks.base import Check
from mxops.smart_values import SmartValue
from mxops.smart_values.native import SmartStr


@dataclass
class SmartCheck(SmartValue):
    """
    Represent a smart value that should result in a check
    """

    @staticmethod
    def type_enforce_value(value: Any) -> Check:
        """
        Convert a value to the expected evaluated type

        :param value: value to convert
        :type value: Any
        :return: converted value
        :rtype: Check
        """
        if isinstance(value, Check):
            return value
        if isinstance(value, dict):
            return instanciate_checks([value])[0]
        raise ValueError(f"Cannot create a check from type {type(value)} ({value})")

    def evaluate(self):
        """
        Evaluate the raw value and save the intermediary values until a
        dict is reached. The keys of this dictionnary are fully evaluated as
        SmartString as they should be the kwargs of a Check.
        The responsibility of the evaluation of the value of the kwargs is left to the
        Check class
        """

        def result_is_not_dict_or_check(
            _previous_value: Any, current_value: Any
        ) -> bool:
            return not isinstance(current_value, (dict, Check))

        self._conditional_evaluation(result_is_not_dict_or_check)

        current_value = self.get_evaluated_value()
        if isinstance(current_value, dict):
            current_value_as_tuple = [
                (SmartStr(k), v) for k, v in current_value.items()
            ]
            [k.evaluate() for k, _v in current_value_as_tuple]
            current_value = {
                k.get_evaluated_value(): v for k, v in current_value_as_tuple
            }
            if current_value != self.get_evaluated_value():
                self.evaluated_values.append(current_value)
        self._enforce_add_value()

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
    Represent a smart value that should result in a list of checks
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
        for raw_check in list(value):
            check = SmartCheck(raw_check)
            check.evaluate()
            result.append(check.get_evaluated_value())
        return result

    def get_evaluated_value(self) -> list[Check]:
        """
        Return the evaluated value

        :return: evaluated value
        :rtype: list[Check]
        """
        return super().get_evaluated_value()

    def evaluate(self):
        """
        Evaluate the raw value and save the intermediary values until a
        list is reached. The evaluation of the element of the list is a
        responsibility left to the SmartCheck class
        """

        def result_is_not_list_or_set(_previous_value: Any, current_value: Any) -> bool:
            return not isinstance(current_value, (list, set))

        self._conditional_evaluation(result_is_not_list_or_set)
        self._enforce_add_value()


def instanciate_checks(raw_checks: list[dict]) -> list[Check]:
    """
    Take checks as dictionaries and convert them to their corresponding check classes.

    :param raw_checks: checks to instantiate
    :type raw_checks: list[dict]
    :return: checks instances
    :rtype: list[Check]
    """
    checks_list = []
    for source_raw_check in raw_checks:
        raw_check = deepcopy(source_raw_check)
        try:
            check_type: str = raw_check.pop("type")
        except KeyError as err:
            raise errors.InvalidCheckDefinition("check", raw_check) from err
        check_class_name = (
            check_type if check_type.endswith("Check") else check_type + "Check"
        )
        try:
            module = importlib.import_module("mxops.execution.checks")
            check_class_object = getattr(module, check_class_name)
        except (ImportError, AttributeError) as err:
            raise errors.UnkownCheck(check_type) from err
        try:
            checks_list.append(check_class_object(**raw_check))
        except Exception as err:
            raise errors.InvalidCheckDefinition(check_type, raw_check) from err
    return checks_list
