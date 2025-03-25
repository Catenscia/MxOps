"""
author: Etienne Wallet

This module contains base smart values that are used to construct other smart values
"""

from dataclasses import dataclass, field
from typing import Any, Callable
from mxops import errors
from mxops.smart_values.utils import (
    force_str,
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
        evaluation_str = force_str(evaluated_value)
        middle_values_str = []
        previous_str = None
        for mid_val in [self.raw_value, *self.evaluated_values]:
            mid_val_str = replace_escaped_characters(force_str(mid_val))
            if mid_val_str in (evaluation_str, previous_str):
                continue
            previous_str = mid_val_str
            middle_values_str.append(mid_val_str)
        if len(middle_values_str) > 0:
            values_str = " -> ".join(s for s in middle_values_str)
            evaluation_str += f" ({values_str})"
        return evaluation_str

    def _conditional_evaluation(self, func: Callable[[Any, Any], bool]):
        """
        Evaluate the raw value and save the intermediary values while the provided
        function returns True

        :param func: function that take as input the previous evaluated value and the
            current evaluated value and return if the evaluation should keep going
        :type func: Callable[[Any, Any], bool]
        """
        k = 0
        self.evaluated_values = []
        previous_value = None
        current_value = self.raw_value
        while func(previous_value, current_value):
            previous_value = current_value
            current_value = retrieve_value_from_any(previous_value)
            self.evaluated_values.append(current_value)
            k += 1
            if k > 1000:
                raise errors.MaxIterationError(
                    f"Unable to evaluated raw value {self.raw_value}"
                )
        if len(self.evaluated_values) == 0:
            self.evaluated_values.append(self.raw_value)

    def _enforce_add_value(self):
        """
        Enforce type on the current value and add it to the evaluated values if
        it differs
        """
        current_value = self.get_evaluated_value()
        enforced_type_value = self.type_enforce_value(current_value)
        if (
            type(enforced_type_value) is not type(current_value)
            or enforced_type_value != current_value
        ):
            self.evaluated_values.append(enforced_type_value)

    def evaluate(self):
        """
        Evaluate the raw value and save the intermediary values until the
        final value is reached (no more modification)
        """

        def result_is_different(previous_value: Any, current_value: Any) -> bool:
            return previous_value != current_value

        self._conditional_evaluation(result_is_different)
        self._enforce_add_value()

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
