"""
This module contains the functions to create Steps
It is separated to avoid having circular import
"""

from dataclasses import dataclass
import importlib
from typing import Any
from mxops import errors
from mxops.execution.smart_values import SmartValue
from mxops.execution.steps.base import Step


@dataclass
class SmartStep(SmartValue):
    """
    Represent a smart value that should result in a step
    """

    @staticmethod
    def type_enforce_value(value: Any) -> Step:
        """
        Convert a value to the expected evaluated type

        :param value: value to convert
        :type value: Any
        :return: converted value
        :rtype: Step
        """
        if isinstance(value, Step):
            return value
        elif isinstance(value, dict):
            return instanciate_steps([value])[0]
        raise ValueError(f"Cannot create a step from type {type(value)} ({value})")

    def get_evaluated_value(self) -> Step:
        """
        Return the evaluated value

        :return: evaluated value
        :rtype: Step
        """
        return super().get_evaluated_value()


@dataclass
class SmartSteps(SmartValue):
    """
    Represent a smart value that should result in a list of steps
    """

    @staticmethod
    def type_enforce_value(value: Any) -> list[Step]:
        """
        Convert a value to the expected evaluated type

        :param value: value to convert
        :type value: Any
        :return: converted value
        :rtype: list[Step]
        """
        result = []
        for raw_step in list(value):
            step = SmartStep(raw_step)
            step.evaluate()
            result.append(step.get_evaluated_value())
        return result

    def get_evaluated_value(self) -> list[Step]:
        """
        Return the evaluated value

        :return: evaluated value
        :rtype: list[Step]
        """
        return super().get_evaluated_value()


def instanciate_steps(raw_steps: list[dict]) -> list[Step]:
    """
    Take steps as dictionaries and convert them to their corresponding step classes.

    :param raw_steps: steps to instantiate
    :type raw_steps: list[dict]
    :return: steps instances
    :rtype: list[Step]
    """
    steps_list = []
    for raw_step in raw_steps:
        step_type: str = raw_step.pop("type")
        if raw_step.pop("skip", False):
            continue
        step_class_name = (
            step_type if step_type.endswith("Step") else step_type + "Step"
        )

        try:
            module = importlib.import_module("mxops.execution.steps")
            step_class_object = getattr(module, step_class_name)
        except (ImportError, AttributeError) as err:
            raise errors.UnkownStep(step_type) from err
        if not issubclass(step_class_object, Step):
            raise errors.UnkownStep(step_type)
        try:
            step = step_class_object(**raw_step)
        except Exception as err:
            raise errors.InvalidStepDefinition(step_type, raw_step) from err
        steps_list.append(step)
    return steps_list
