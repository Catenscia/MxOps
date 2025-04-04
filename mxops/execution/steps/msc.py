"""
author: Etienne Wallet

This module contains miscelanious Steps
"""

from dataclasses import dataclass, field
from importlib.util import spec_from_file_location, module_from_spec
import time
from typing import Any, Iterable

from multiversx_sdk.core.constants import METACHAIN_ID
import numpy as np

from mxops import errors
from mxops.common.providers import MyProxyNetworkProvider
from mxops.config.config import Config
from mxops.data.execution_data import ScenarioData
from mxops.data.utils import json_dumps
from mxops.enums import LogGroupEnum, NetworkEnum
from mxops.execution import utils
from mxops.smart_values import (
    SmartBool,
    SmartDict,
    SmartFloat,
    SmartInt,
    SmartList,
    SmartPath,
    SmartStr,
    SmartValue,
)
from mxops.execution.steps.base import Step
from mxops.execution.steps.factory import SmartSteps
from mxops.smart_values.native import SmartRawDict, SmartRawList


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

    def _get_evaluated_iterable(self) -> Iterable[Any]:
        """
        From the evaluated smart values, return the iterable that this loop
        should use

        :return: iterable
        :rtype: Iterable[Any]
        """
        var_start = (
            None if self.var_start is None else self.var_start.get_evaluated_value()
        )
        var_end = None if self.var_end is None else self.var_end.get_evaluated_value()
        var_list = (
            None if self.var_list is None else self.var_list.get_evaluated_value()
        )
        if var_start is not None and var_end is not None:
            return range(var_start, var_end)
        if var_list is not None:
            return var_list
        raise ValueError("Loop iteration is not correctly defined")

    def _initialize(self):
        """
        initiate the loop variable with a value to avoid pre-evaluation
        error when a sub steps is defined using the loop variable
        """
        self.var_name.evaluate()
        if self.var_start is not None:
            self.var_start.evaluate()
        if self.var_end is not None:
            self.var_end.evaluate()
        if self.var_list is not None:
            self.var_list.evaluate()
        iterable = self._get_evaluated_iterable()
        try:
            first_value = next(iter(iterable))
        except StopIteration:
            first_value = None
        scenario_data = ScenarioData.get()
        scenario_data.set_value(self.var_name.get_evaluated_value(), first_value)

    def generate_steps(self) -> Iterable[Step]:
        """
        Generate the steps that sould be executed

        :yield: steps to be executed
        :rtype: iterable[Step]
        """
        self.evaluate_smart_values()
        var_name = self.var_name.get_evaluated_value()
        iterable = self._get_evaluated_iterable()
        scenario_data = ScenarioData.get()
        for var in iterable:
            scenario_data.set_value(var_name, var)
            self.steps.evaluate()
            yield from self.steps.get_evaluated_value()

    def _execute(self):
        """
        Does nothing and should not be called as the step does nothing in itself
        it is only a shell for other Steps
        """
        logger = ScenarioData.get_scenario_logger(LogGroupEnum.EXEC)
        logger.warning("The execute function of a LoopStep was called")


@dataclass
class SetVarsStep(Step):
    """
    Represents a step to set variables within the Scenario
    """

    variables: SmartRawDict

    def _execute(self):
        """
        Parse the values to be assigned to the given variables
        """
        logger = ScenarioData.get_scenario_logger(LogGroupEnum.EXEC)
        scenario_data = ScenarioData.get()

        for raw_key, raw_value in self.variables.get_evaluated_value().items():
            smart_key = SmartStr(raw_key)
            smart_key.evaluate()
            smart_value = SmartValue(raw_value)
            smart_value.evaluate()
            key = smart_key.get_evaluated_value()
            value = smart_value.get_evaluated_value()
            logger.info(f"Setting variable `{key}` with the value `{value}`")
            scenario_data.set_value(key, value)


@dataclass
class WaitStep(Step):
    """
    Represent a step to wait until a condition is fulfilled
    """

    for_seconds: SmartFloat | None = field(default=None)
    for_blocks: SmartInt | None = field(default=None)
    shard: SmartInt = METACHAIN_ID

    def _execute(self):
        """
        Wait until the specified condition is met
        """
        logger = ScenarioData.get_scenario_logger(LogGroupEnum.EXEC)
        if self.for_seconds is not None:
            for_seconds = self.for_seconds.get_evaluated_value()
            logger.info(f"Waiting for {for_seconds} seconds")
            time.sleep(for_seconds)
            return
        if self.for_blocks is not None:
            for_blocks = self.for_blocks.get_evaluated_value()
            network = Config.get_config().get_network()
            shard = self.shard.get_evaluated_value()
            logger.info(f"Waiting for {for_blocks} blocks on shard {shard}")
            if network == NetworkEnum.CHAIN_SIMULATOR:
                MyProxyNetworkProvider().generate_blocks(for_blocks)
            else:
                utils.wait_for_n_blocks(shard, for_blocks)
        else:
            raise ValueError(
                "Either for_seconds or for_blocks must have a value different from None"
            )


@dataclass
class PythonStep(Step):
    """
    This Step execute a custom python function of the user
    """

    module_path: SmartPath
    function: SmartStr
    arguments: SmartList = field(default_factory=lambda: SmartList([]))
    keyword_arguments: SmartDict = field(default_factory=lambda: SmartDict({}))
    log_result: SmartBool = True
    result_save_key: SmartStr | None = None

    def _execute(self):
        """
        Execute the specified function
        """
        logger = ScenarioData.get_scenario_logger(LogGroupEnum.EXEC)
        module_path = self.module_path.get_evaluated_value()
        module_name = module_path.stem
        function = self.function.get_evaluated_value()
        logger.info(
            f"Executing python function {function} from user module {module_name}"
        )

        # load module and function
        spec = spec_from_file_location(module_name, module_path.as_posix())
        user_module = module_from_spec(spec)
        spec.loader.exec_module(user_module)
        user_function = getattr(user_module, function)

        # transform args and kwargs and execute
        arguments = self.arguments.get_evaluated_value()
        keyword_arguments = self.keyword_arguments.get_evaluated_value()
        result = user_function(*arguments, **keyword_arguments)

        if self.result_save_key is not None:
            result_save_key = self.result_save_key.get_evaluated_value()
            scenario_data = ScenarioData.get()
            scenario_data.set_value(result_save_key, result)
            logger.info(
                f"Saving function result at {result_save_key}: {json_dumps(result)}"
            )
        elif self.log_result.get_evaluated_value():
            logger.info(f"Function result: {json_dumps(result)}")


@dataclass
class SceneStep(Step):
    """
    This Step does nothing asside holding a variable
    with the path of the scene. The actual action is operated at the scene level.
    """

    path: SmartPath
    repeat: SmartInt = 1

    def _execute(self):
        """
        Does nothing and should not be called
        """
        logger = ScenarioData.get_scenario_logger(LogGroupEnum.EXEC)
        logger.warning("The execute function of a SceneStep was called")


@dataclass
class SetSeedStep(Step):
    """
    Represents a step to set the random seed
    """

    seed: SmartInt

    def _execute(self):
        """
        set the random seed
        """
        seed = self.seed.get_evaluated_value()
        np.random.seed(seed)
        logger = ScenarioData.get_scenario_logger(LogGroupEnum.EXEC)
        logger.info(f"Random seed has been set to {seed}")


@dataclass
class AssertStep(Step):
    """
    Represents a step that check assertion
    """

    expressions: SmartRawList

    def _execute(self):
        """
        set the random seed
        """
        logger = ScenarioData.get_scenario_logger(LogGroupEnum.EXEC)
        expressions = self.expressions.get_evaluated_value()
        for expression in expressions:
            smart_value = SmartBool(expression)
            smart_value.evaluate()
            if smart_value.get_evaluated_value() is not True:
                raise errors.AssertionFailed(smart_value.get_evaluation_string())
            logger.info(f"Assertion {expression} is True")


@dataclass
class LogStep(Step):
    """
    Represents a step that logs user input
    """

    error: SmartStr | None = None
    warning: SmartStr | None = None
    info: SmartStr | None = None
    debug: SmartStr | None = None

    def _execute(self):
        """
        set the random seed
        """
        logger = ScenarioData.get_scenario_logger(LogGroupEnum.EXEC)
        if self.error is not None:
            logger.error(self.error.get_evaluated_value())
        if self.warning is not None:
            logger.warning(self.warning.get_evaluated_value())
        if self.info is not None:
            logger.info(self.info.get_evaluated_value())
        if self.debug is not None:
            logger.debug(self.debug.get_evaluated_value())
