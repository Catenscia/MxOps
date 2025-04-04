"""
author: Etienne Wallet

Errors used in the MxOps package
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from multiversx_sdk import Address, TransactionOnNetwork

from mxops.enums import NetworkEnum
from mxops.utils.msc import get_tx_link


#############################################################
#
#                   Operation Errors
#
#############################################################


class ParsingError(Exception):
    """
    To be raised when some data could not be parsed successfully
    """

    def __init__(
        self,
        raw_object: Any,
        parsing_target: str,
    ) -> None:
        message = f"Could not parse {raw_object} as {parsing_target}"
        super().__init__(message)


class TokenNotFound(Exception):
    """
    To be raised when an expected token was not found
    """


class FaucetFailed(Exception):
    """
    To be raised when a faucet did not succeed
    """


class NewTokenIdentifierNotFound(Exception):
    """
    To be raised when the token identifier of newly issued token was not found in
    the results of the transaction
    """


class MaxIterations(Exception):
    """
    To be raised when some operations has reached too many operations
    """


class SmartValueNotEvaluated(Exception):
    """
    To be raised when a smart values was asked for its evaluations
    but it has yet to be evaluated
    """


class MaxIterationError(Exception):
    """
    To be raised when too many iteration have been executed
    """


class ClosingCharNotFound(Exception):
    """
    To be raised when a closing character could not be found in a given string
    """

    def __init__(self, string: str, closing_char: str) -> None:
        message = (
            f"Could not find a closing char '{closing_char}' for string '{string}'"
        )
        super().__init__(message)


#############################################################
#
#                   Data Management Errors
#
#############################################################


class UnknownScenario(Exception):
    """
    To be raised when a specified scenario is not found
    """

    def __init__(self, scenario_name: str) -> None:
        message = f"Scenario {scenario_name} is unkown"
        super().__init__(message)


class UnloadedScenario(Exception):
    """
    To be raised when the scenario data was asked before being loaded
    """

    def __init__(self) -> None:
        message = "Scenario data was not loaded"
        super().__init__(message)


class UnknownAccount(Exception):
    """
    To be raised when a specified account is not found in a scenario
    """

    def __init__(self, scenario_name: str, account_designation: str | Address) -> None:
        if isinstance(account_designation, Address):
            account_designation = account_designation.to_bech32()
        message = f"Account {account_designation} is unkown in scenario {scenario_name}"
        super().__init__(message)


class UnknownAbiContract(Exception):
    """
    To be raised when the abi of a specified contract is not found in a scenario
    """

    def __init__(self, scenario_name: str, contract_address: Address) -> None:
        message = (
            f"No ABI found for contract {contract_address.to_bech32()} is "
            f"unkown in scenario {scenario_name}"
        )
        super().__init__(message)


class AccoundIdAlreadyExists(Exception):
    """
    To be raised when trying to assign a new id that already exist
    """

    def __init__(self, account_id: str) -> None:
        message = f"Account id {account_id} already exists"
        super().__init__(message)


class AccoundIdAlreadyhasBech32(Exception):
    """
    To be raised when there is a conflict with an account id
    """

    def __init__(self, account_id: str, existing_bech32: str, new_bech32: str) -> None:
        message = (
            f"Account id {account_id} already had the address {existing_bech32}"
            f"when trying to set it to the address {new_bech32}"
        )
        super().__init__(message)


class AccountAlreadyHasId(Exception):
    """
    To be raised when there is a conflict with an account bech32
    """

    def __init__(self, contract_bech32: str, existing_id: str, new_id: str) -> None:
        message = (
            f"Account {contract_bech32} already had the id {existing_id}"
            f" when trying to set the id {new_id}"
        )
        super().__init__(message)


class UnknownToken(Exception):
    """
    To be raised when a specified token is not found in a scenario
    """

    def __init__(self, scenario_name: str, token_name: str) -> None:
        message = f"Token named {token_name} is unkown in scenario {scenario_name}"
        super().__init__(message)


class TokenNameAlreadyExists(Exception):
    """
    To be raised when there is a conflict with token name
    """

    def __init__(self, token_name: str) -> None:
        message = f"Token named {token_name} already exists"
        super().__init__(message)


class UnknownRootName(Exception):
    """
    To be raised when a specified root name is not found in a scenario
    """

    def __init__(self, scenario_name: str, root_name: str) -> None:
        message = f"Root named {root_name} is unkown in scenario {scenario_name}"
        super().__init__(message)


class ScenarioNameAlreadyExists(Exception):
    """
    To be raised when there is a conflict with scenario name
    """

    def __init__(self, scenario_name: str) -> None:
        message = f"Scenario name {scenario_name} already exists"
        super().__init__(message)


class WrongScenarioDataReference(Exception):
    """
    To be raised when a reference to some scenario data could not
    be parsed correctly
    """

    def __init__(self) -> None:
        message = (
            "Scenario data reference must have the format "
            r'"%<value_key>[:optional_format]"'
        )
        super().__init__(message)


class ForbiddenSceneNetwork(Exception):
    """
    To be raised when a scene was set to be executed on
    a network that the scene does not allow
    """

    def __init__(
        self, path: Path, network_name: str, allowed_networks: list[str]
    ) -> None:
        message = (
            f"Scene {path} not allowed to be executed "
            f"in the network {network_name}.\n"
            f"Allowed networks: {allowed_networks}"
        )
        super().__init__(message)


class ForbiddenSceneScenario(Exception):
    """
    To be raised when a scene was set to be executed in
    a scenario that the scene does not allow
    """

    def __init__(
        self, path: Path, scenario_name: str, allowed_scenario: list[str]
    ) -> None:
        message = (
            f"Scene {path} not allowed to be executed "
            f"in the scenario {scenario_name}.\n"
            f"Allowed scenario: {allowed_scenario}"
        )
        super().__init__(message)


class WrongDataKeyPath(Exception):
    """
    To be raised when a key path does not correspond to the saved
    data
    """


class NoDataForContract(Exception):
    """
    To be raised when a specified contract has no data saved (analyze submodule)
    """

    def __init__(self, contract_bech32_address: str) -> None:
        message = f"Contract {contract_bech32_address} has no saved data"
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
        return f"Error on transaction {get_tx_link(self.tx.hash.hex())}\n"


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


class QueryFailed(Exception):
    """
    To be raised when a query failed
    """


#############################################################
#
#                   Check Errors
#
#############################################################


class CheckFailed(Exception):
    """
    To be raised when an on-chain transaction check fails
    """

    def __init__(self, check: dataclass, tx: TransactionOnNetwork) -> None:
        self.check = check
        self.tx = tx
        super().__init__()

    def __str__(self) -> str:
        return (
            f"Check failed on transaction {get_tx_link(self.tx.hash.hex())}"
            f"\nCheck: {self.check}"
        )


class FuzzTestFailed(Exception):
    """
    To be raised when a fuzz test fails
    """


class AssertionFailed(Exception):
    """
    To be raised when an assertion is not True
    """

    def __init__(self, evaluation_string: str) -> None:
        self.evaluation_string = evaluation_string
        super().__init__()

    def __str__(self) -> str:
        return f"Assertion failed: {self.evaluation_string}"


#############################################################
#
#                   User Errors
#
#############################################################


class UnkownStep(Exception):
    """
    to be raised when the user provide a step name that is unkown
    """

    def __init__(self, step_name: str) -> None:
        self.step_name = step_name
        super().__init__()

    def __str__(self) -> str:
        return f"Unkown Step name: {self.step_name}"


class UnkownCheck(Exception):
    """
    to be raised when the user provide a check name that is unkown
    """

    def __init__(self, check_name: str) -> None:
        self.check_name = check_name
        super().__init__()

    def __str__(self) -> str:
        return f"Unkown Check name: {self.check_name}"


class UnkownVariable(Exception):
    """
    to be raised when the user provide a variable name that is unkown
    """

    def __init__(self, var_name: str) -> None:
        self.step_name = var_name
        super().__init__()

    def __str__(self) -> str:
        return f"Unkown variable: {self.step_name}"


class InvalidStepDefinition(Exception):
    """
    to be raised when the arguments provided by the user for a Step are not valid
    """

    def __init__(self, step_name: str, parameters: dict) -> None:
        self.step_name = step_name
        self.parameters = parameters
        super().__init__()

    def __str__(self) -> str:
        return f"Step {self.step_name} received invalid parameters {self.parameters}"


class InvalidCheckDefinition(Exception):
    """
    to be raised when the arguments provided by the user for a Check are not valid
    """

    def __init__(self, check_name: str, parameters: dict) -> None:
        self.check_name = check_name
        self.parameters = parameters
        super().__init__()

    def __str__(self) -> str:
        return f"Check {self.check_name} received invalid parameters {self.parameters}"


class InvalidQueryResultsDefinition(Exception):
    """
    to be raise when the results types of a query are not correctly defined
    """


class InvalidSceneDefinition(Exception):
    """
    to be raise when a scene is not correctly defined
    """


class InvalidDataFormat(Exception):
    """
    to be raise when the data format is invalid
    """


class WrongFuzzTestFile(Exception):
    """
    to be raised when the file given for fuzz testing in not correctly formatted
    """


class WalletAlreadyExist(Exception):
    """
    to be raised when a wallet was asked to be generated but a wallet already exists
    at that location
    """

    def __init__(self, wallet_path: Path) -> None:
        self.wallet_path = wallet_path
        super().__init__()

    def __str__(self) -> str:
        return f"A wallet already exists at {self.wallet_path}"


class WrongNetworkForStep(Exception):
    """
    to be raised when a step was asked to be executed in an innapropriate network
    """

    def __init__(
        self, current_network: NetworkEnum, allowed_networks: list[NetworkEnum]
    ):
        self.current_network = current_network
        self.allowed_networks = allowed_networks
        super().__init__()

    def __str__(self) -> str:
        return (
            f"Step can only be executed in the newtorks {self.allowed_networks},"
            f" while current network is {self.current_network}"
        )
