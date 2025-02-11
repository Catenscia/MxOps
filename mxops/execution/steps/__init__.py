"""
author: Etienne Wallet

This subpackage contains all the steps that can be used with MxOps
"""

from mxops.execution.steps.msc import (
    LoopStep,
    PythonStep,
    SetVarsStep,
    WaitStep,
    SceneStep,
)
from mxops.execution.steps.setup import (
    ChainSimulatorFaucetStep,
    GenerateWalletsStep,
    R3D4FaucetStep,
)
from mxops.execution.steps.smart_contract import (
    ContractCallStep,
    ContractDeployStep,
    ContractQueryStep,
    ContractUpgradeStep,
    FileFuzzerStep,
)
from mxops.execution.steps.transactions import TransferStep
from mxops.execution.steps.token_management import (
    FungibleIssueStep,
    SemiFungibleIssueStep,
    NonFungibleIssueStep,
    MetaIssueStep,
    ManageFungibleTokenRolesStep,
    ManageNonFungibleTokenRolesStep,
    ManageSemiFungibleTokenRolesStep,
    ManageMetaTokenRolesStep,
    FungibleMintStep,
    NonFungibleMintStep,
)

__all__ = [
    "ChainSimulatorFaucetStep",
    "ContractCallStep",
    "ContractDeployStep",
    "ContractQueryStep",
    "ContractUpgradeStep",
    "FileFuzzerStep",
    "FungibleIssueStep",
    "FungibleMintStep",
    "GenerateWalletsStep",
    "LoopStep",
    "ManageFungibleTokenRolesStep",
    "ManageMetaTokenRolesStep",
    "ManageNonFungibleTokenRolesStep",
    "ManageSemiFungibleTokenRolesStep",
    "MetaIssueStep",
    "NonFungibleIssueStep",
    "NonFungibleMintStep",
    "PythonStep",
    "R3D4FaucetStep",
    "SceneStep",
    "SemiFungibleIssueStep",
    "SetVarsStep",
    "TransferStep",
    "WaitStep",
]
