"""
author: Etienne Wallet

Errors used in the MxOps package
"""
from pathlib import Path
from typing import List

from multiversx_sdk_network_providers.transactions import TransactionOnNetwork

from mxops.utils.msc import get_tx_link

#############################################################
#
#                   Data Managment Errors
#
#############################################################


class UnknownScenario(Exception):
    """
    To be raised when a specified scenario is not found
    """

    def __init__(self, scenario_name: str) -> None:
        message = (f'Scenario {scenario_name} is unkown')
        super().__init__(message)


class UnloadedScenario(Exception):
    """
    To be raised when the scenario data was asked before being loaded
    """

    def __init__(self) -> None:
        message = 'Scenario data was not loaded'
        super().__init__(message)


class UnknownContract(Exception):
    """
    To be raised when a specified contract is not found is a scenario
    """

    def __init__(self, scenario_name: str, contract_id: str) -> None:
        message = (f'Contract {contract_id} is unkown in '
                   f'scenario {scenario_name}')
        super().__init__(message)


class UnknownAccount(Exception):
    """
    To be raised when a specified account is not found in a scene
    """

    def __init__(self, account_name: str) -> None:
        message = f'Account {account_name} is unkown in the current scene'
        super().__init__(message)


class ContractIdAlreadyExists(Exception):
    """
    To be raised when there is a conflict with contract id
    """

    def __init__(self, contract_id: str) -> None:
        message = f'Contract id {contract_id} already exists'
        super().__init__(message)


class ScenarioNameAlreadyExists(Exception):
    """
    To be raised when there is a conflict with scenario name
    """

    def __init__(self, scenario_name: str) -> None:
        message = f'Scenario name {scenario_name} already exists'
        super().__init__(message)


class WrongScenarioDataReference(Exception):
    """
    To be raised when a reference to some scenario data could not
    be parsed correctly
    """

    def __init__(self) -> None:
        message = ('Scenario data reference must have the format '
                   r'"%contract_id%valuekey[:optional_format]"')
        super().__init__(message)


class ForbiddenSceneNetwork(Exception):
    """
    To be raised when a scene was set to be executed on
    a network that the scene does not allow
    """

    def __init__(self, scene_path: Path, network_name: str, allowed_networks: List[str]) -> None:
        message = (f'Scene {scene_path} not allowed to be executed '
                   f'in the network {network_name}.\n'
                   f'Allowed networks: {allowed_networks}'
                   )
        super().__init__(message)


class ForbiddenSceneScenario(Exception):
    """
    To be raised when a scene was set to be executed in
    a scenario that the scene does not allow
    """

    def __init__(self, scene_path: Path, scenario_name: str, allowed_scenario: List[str]) -> None:
        message = (f'Scene {scene_path} not allowed to be executed '
                   f'in the scenario {scenario_name}.\n'
                   f'Allowed scenario: {allowed_scenario}'
                   )
        super().__init__(message)

#############################################################
#
#                   Transactions Errors
#
#############################################################


class TransactionError(Exception):
    """
    To be raised when a transaction encountered an error
    on the network
    """

    def __init__(self, tx: TransactionOnNetwork) -> None:
        self.tx = tx
        super().__init__()

    def __str__(self) -> str:
        return f'Error on transaction {get_tx_link(self.tx.hash)}\n'


class FailedTransactionError(TransactionError):
    """
    To be raised when a transaction send got a failed status
    """


class InvalidTransactionError(TransactionError):
    """
    To be raised when a transaction send got an invalid status
    """


class UnfinalizedTransactionException(TransactionError):
    """
    To be raised when a transaction was found to be
    not finalized (completed tx excepted)
    """


class SmartContractExecutionError(TransactionError):
    """
    To be raised when a transaction encountered a smart
    contract execution error
    """


class InternalVmExecutionError(TransactionError):
    """
    To be raised when a transaction encountered an internal
    VM execution error
    """


class TransactionExecutionError(TransactionError):
    """
    To be raised when a transaction encountered an internal
    VM execution error
    """


class EmptyQueryResults(Exception):
    """
    To be raised when a query returned no results
    """
