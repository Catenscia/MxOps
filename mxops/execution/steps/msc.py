"""
author: Etienne Wallet

This module contains miscelanious Steps
"""

from dataclasses import dataclass
from typing import Iterator

from mxops.data.execution_data import ScenarioData
from mxops.execution.smart_values import (
    SmartDict,
    SmartInt,
    SmartStr,
    SmartValue,
)
from mxops.execution.steps.base import Step
from mxops.execution.steps.factory import SmartSteps
from mxops.utils.logger import get_logger

LOGGER = get_logger("msc steps")


@dataclass
class LoopStep(Step):
    """
    Represents a set of steps to execute several time
    """

    steps: SmartSteps
    var_name: SmartStr
    var_start: SmartInt | None = None
    var_end: SmartInt | None = None
    var_list: SmartValue | None = None

    def generate_steps(self) -> Iterator[Step]:
        """
        Generate the steps that sould be executed

        :yield: steps to be executed
        :rtype: Iterator[Step]
        """
        self.evaluate_smart_values()
        var_name = self.var_name.get_evaluated_value()
        var_start = (
            None if self.var_start is None else self.var_start.get_evaluated_value()
        )
        var_end = None if self.var_end is None else self.var_end.get_evaluated_value()
        var_list = (
            None if self.var_list is None else self.var_list.get_evaluated_value()
        )
        if var_start is not None and var_end is not None:
            iterator = range(var_start, var_end)
        elif var_list is not None:
            iterator = var_list
        else:
            raise ValueError("Loop iteration is not correctly defined")
        scenario_data = ScenarioData.get()
        for var in iterator:
            scenario_data.set_value(var_name, var)
            for step in self.steps.get_evaluated_value():
                yield step

    def _execute(self):
        """
        Does nothing and should not be called as the step does nothing in itself
        it is only a shell for other Steps
        """
        LOGGER.warning("The execute function of a LoopStep was called")


@dataclass
class SetVarsStep(Step):
    """
    Represents a step to set variables within the Scenario
    """

    variables: SmartDict

    def _execute(self):
        """
        Parse the values to be assigned to the given variables
        """
        scenario_data = ScenarioData.get()

        for key, value in self.variables.get_evaluated_value().items():
            LOGGER.info(f"Setting variable `{key}` with the value `{value}`")
            scenario_data.set_value(key, value)
