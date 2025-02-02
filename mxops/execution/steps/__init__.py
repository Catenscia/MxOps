"""
author: Etienne Wallet

This subpackage contains all the steps that can be used with MxOps
"""

from mxops.execution.steps.msc import LoopStep, PythonStep, SetVarsStep, WaitStep
from mxops.execution.steps.setup import GenerateWalletsStep
from mxops.execution.steps.smart_contract import (
    ContractCallStep,
    ContractDeployStep,
    ContractQueryStep,
    ContractUpgradeStep,
)
from mxops.execution.steps.transactions import TransferStep

__all__ = [
    "ContractCallStep",
    "ContractDeployStep",
    "ContractQueryStep",
    "ContractUpgradeStep",
    "GenerateWalletsStep",
    "LoopStep",
    "PythonStep",
    "SetVarsStep",
    "TransferStep",
    "WaitStep",
]
