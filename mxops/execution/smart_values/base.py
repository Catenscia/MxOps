"""
author: Etienne Wallet

This module contains base smart values that are used to construct other smart values
"""

from dataclasses import dataclass, field
from typing import Any
from mxops import errors
from mxops.execution.smart_values.utils import (
    replace_escaped_characters,
    retrieve_value_from_any,
)


@dataclass
class SmartValue:
    """
    Represent a smart value that can have any type
    """

    raw_value: Any
    evaluated_values: list | None = field(init=False, default=None)

    @property
    def is_evaluated(self) -> bool:
        """
        If the smart value has been evaluated

        :return: true if evaluated
        :rtype: bool
        """
        return self.evaluated_values is not None

    def require_evaluated(self):
        """
        Raise an error if the value has not been evaluated
        """
        if not self.is_evaluated:
            raise errors.SmartValueNotEvaluated

    def get_evaluation_string(self):
        """
        construct the string the show the different values that the raw_value
        has beed evaluated to.
        Ex "USDT-123456 (%{%{Bob-token}.identifier} -> %usdt.identifier)"
        """
        self.require_evaluated()
        evaluated_value = self.get_evaluated_value()
        evaluation_str = str(evaluated_value)
        middle_values_str = []
        previous_str = None
        for mid_val in [self.raw_value, *self.evaluated_values]:
            mid_val_str = replace_escaped_characters(str(mid_val))
            if mid_val_str in (evaluation_str, previous_str):
                continue
            previous_str = mid_val_str
            middle_values_str.append(mid_val_str)
        if len(middle_values_str) > 0:
            values_str = " -> ".join(s for s in middle_values_str)
            evaluation_str += f" ({values_str})"
        return evaluation_str

    def evaluate(self):
        """
        Evaluate the raw value and save the intermediary values until the
        final value is reached
        """
        k = 0
        self.evaluated_values = []
        last_value = None
        result = self.raw_value
        while result != last_value:
            last_value = result
            result = retrieve_value_from_any(last_value)
            self.evaluated_values.append(result)
            k += 1
            if k > 1000:
                raise errors.MaxIterationError(
                    f"Unable to evaluated raw value {self.raw_value}"
                )
        enforced_type_value = self.type_enforce_value(last_value)
        if (
            type(enforced_type_value) is not type(last_value)
            or enforced_type_value != last_value
        ):
            self.evaluated_values.append(enforced_type_value)

    @staticmethod
    def type_enforce_value(value: Any) -> Any:
        """
        Convert a value to the expected evaluated type

        :param value: value to convert
        :type value: Any
        :return: converted value
        :rtype: Any
        """
        return value

    def get_evaluated_value(self) -> Any:
        """
        Return the evaluated value

        :return: evaluated value
        :rtype: Any
        """
        self.require_evaluated()
        return self.evaluated_values[-1]
