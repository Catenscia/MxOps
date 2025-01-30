"""
author: Etienne Wallet

This module contains the classes used to execute scenes in a scenario
"""

from __future__ import annotations
from dataclasses import dataclass, field
from importlib.util import spec_from_file_location, module_from_spec
import os
from pathlib import Path
import sys
import time
from typing import Any, ClassVar, Iterator

from multiversx_sdk import (
    Address,
    SmartContractTransactionsFactory,
    SmartContractTransactionsOutcomeParser,
    SmartContractController,
    Token,
    TokenManagementTransactionsFactory,
    TokenTransfer,
    Transaction,
    TransactionOnNetwork,
    TransactionsFactoryConfig,
    TransferTransactionsFactory,
    TokenManagementTransactionsOutcomeParser,
)
from multiversx_sdk.abi import Abi, Serializer, U64Value
from multiversx_sdk.core.constants import METACHAIN_ID
from multiversx_sdk.core.errors import BadAddressError
import requests
import yaml

from mxops.common.providers import MyProxyNetworkProvider
from mxops.config.config import Config
from mxops.data.execution_data import InternalContractData, ScenarioData, TokenData
from mxops.data.utils import convert_mx_data_to_vanilla, json_dumps
from mxops.enums import NetworkEnum, TokenTypeEnum
from mxops.execution import utils

from mxops.execution.account import AccountsManager
from mxops.execution.checks import Check, SuccessCheck, instanciate_checks
from mxops.execution.msc import EsdtTransfer
from mxops.execution.network import send, send_and_wait_for_result
from mxops.utils.logger import get_logger
from mxops.utils.msc import get_file_hash, get_tx_link
from mxops import errors
from mxops.utils.wallets import generate_pem_wallet

LOGGER = get_logger("steps")


@dataclass
class Step:
    """
    Represents an instruction to execute within a scene
    """

    def execute(self):
        """
        Interface for the method to execute the action described by a Step instance.
        Each child class must overrid this method

        :raises NotImplementedError: if this method was not overriden
        by a child class or directly executed.
        """
        raise NotImplementedError

    @classmethod
    def from_dict(cls, data: dict) -> Step:
        """
        Instantiate a Step instance from a dictionary

        :param data: data used as kwargs to instantiate the Step
        :type data: dict
        :return: step instance
        :rtype: Step
        """
        return cls(**data)


@dataclass(kw_only=True)
class TransactionStep(Step):
    """
    Represents a step that produces and send a transaction
    """

    sender: str
    checks: list[Check] = field(default_factory=lambda: [SuccessCheck()])

    def __post_init__(self):
        """
        After the initialisation of an instance, if the checks are
        found to be dict, will try to convert them to Checks instances.
        Usefull for easy loading from yaml files
        """
        if len(self.checks) > 0 and isinstance(self.checks[0], dict):
            self.checks = instanciate_checks(self.checks)

    def build_unsigned_transaction(self) -> Transaction:
        """
        Interface for the method that will build transaction to send. This transaction
        is meant to contain all the data specific to this Step.
        The signature will be done at a later stage in the method sign_transaction

        :return: transaction created by the Step
        :rtype: Transaction
        """
        raise NotImplementedError

    def set_nonce_and_sign_transaction(self, tx: Transaction):
        """
        Sign the transaction created by this step and update the account nonce

        :param tx: tra
        :type tx: Transaction
        """
        sender = utils.retrieve_value_from_string(self.sender)
        sender_account = AccountsManager.get_account(sender)
        tx.nonce = sender_account.get_nonce_then_increment()
        tx.signature = sender_account.sign_transaction(tx)

    def _post_transaction_execution(self, on_chain_tx: TransactionOnNetwork | None):
        """
        Interface for the function that will be executed after the transaction has
        been successfully executed

        :param on_chain_tx: on chain transaction that was sent by the Step
        :type on_chain_tx: TransactionOnNetwork | None
        """
        # by default, do nothing

    def execute(self):
        """
        Execute the workflow for a transaction Step: build, send, check
        and post execute
        """
        tx = self.build_unsigned_transaction()
        self.set_nonce_and_sign_transaction(tx)

        if len(self.checks) > 0:
            on_chain_tx = send_and_wait_for_result(tx)
            for check in self.checks:
                check.raise_on_failure(on_chain_tx)
            LOGGER.info(
                f"Transaction successful: {get_tx_link(on_chain_tx.hash.hex())}"
            )
        else:
            on_chain_tx = None
            send(tx)
            LOGGER.info("Transaction sent")

        self._post_transaction_execution(on_chain_tx)


@dataclass
class LoopStep(Step):
    """
    Represents a set of steps to execute several time
    """

    steps: list[Step]
    var_name: str
    var_start: Any = None
    var_end: Any = None
    var_list: Any = None

    def generate_steps(self) -> Iterator[Step]:
        """
        Generate the steps that sould be executed

        :yield: steps to be executed
        :rtype: Iterator[Step]
        """
        var_name = utils.retrieve_value_from_any(self.var_name)
        var_start = utils.retrieve_value_from_any(self.var_start)
        var_end = utils.retrieve_value_from_any(self.var_end)
        var_list = utils.retrieve_value_from_any(self.var_list)
        if var_start is not None and var_end is not None:
            iterator = range(var_start, var_end)
        elif var_list is not None:
            iterator = utils.retrieve_value_from_any(var_list)
        else:
            raise ValueError("Loop iteration is not correctly defined")
        scenario_data = ScenarioData.get()
        for var in iterator:
            scenario_data.set_value(var_name, var)
            for step in self.steps:
                yield step

    def execute(self):
        """
        Does nothing and should not be called. It is still implemented to avoid the
        warning W0622.
        """
        LOGGER.warning("The execute function of a SceneStep was called")

    def __post_init__(self):
        """
        After the initialisation of an instance, if the inner steps are
        found to be dict, will try to convert them to Steps instances.
        Usefull for easy loading from yaml files
        """
        if len(self.steps) > 0 and isinstance(self.steps[0], dict):
            self.steps = instanciate_steps(self.steps)


@dataclass
class ContractDeployStep(TransactionStep):
    """
    Represents a smart contract deployment
    """

    wasm_path: str
    contract_id: str
    gas_limit: int
    abi_path: str | None = None
    upgradeable: bool = True
    readable: bool = True
    payable: bool = False
    payable_by_sc: bool = False
    arguments: list[Any] = field(default_factory=list)

    def build_unsigned_transaction(self) -> Transaction:
        """
        Build the transaction for a contract deployment

        :return: transaction built
        :rtype: Transaction
        """
        LOGGER.info(f"Deploying contract {self.contract_id}")
        scenario_data = ScenarioData.get()

        # check that the id of the contract is free
        contract_id = utils.retrieve_value_from_any(self.contract_id)
        try:
            scenario_data.get_contract_value(contract_id, "address")
            raise errors.ContractIdAlreadyExists(contract_id)
        except errors.UnknownContract:
            pass

        if self.abi_path is not None:
            abi = Abi.load(Path(self.abi_path))
        else:
            abi = None

        factory_config = TransactionsFactoryConfig(Config.get_config().get("CHAIN"))
        sc_factory = SmartContractTransactionsFactory(factory_config, abi=abi)
        bytecode = Path(self.wasm_path).read_bytes()

        retrieved_arguments = utils.retrieve_value_from_any(self.arguments)

        return sc_factory.create_transaction_for_deploy(
            sender=utils.get_address_instance(self.sender),
            bytecode=bytecode,
            arguments=retrieved_arguments,
            gas_limit=self.gas_limit,
            is_upgradeable=self.upgradeable,
            is_readable=self.readable,
            is_payable=self.payable,
            is_payable_by_sc=self.payable_by_sc,
        )

    def _post_transaction_execution(self, on_chain_tx: TransactionOnNetwork | None):
        """
        Save the new contract data in the Scenario

        :param on_chain_tx: successful deployment transaction
        :type on_chain_tx: TransactionOnNetwork | None
        """
        if not isinstance(on_chain_tx, TransactionOnNetwork):
            raise ValueError("On chain transaction is None")
        scenario_data = ScenarioData.get()

        # save the abi
        contract_id = utils.retrieve_value_from_any(self.contract_id)
        scenario_data.set_contract_abi_from_source(contract_id, self.abi_path)

        # get the new deployed address
        parser = SmartContractTransactionsOutcomeParser()
        parsed_outcome = parser.parse_deploy(on_chain_tx)
        try:
            parsed_contract = parsed_outcome.contracts[0]
            contract_address = parsed_contract.address
        except (IndexError, BadAddressError) as err:
            raise errors.ParsingError(
                parsed_outcome, "contract deployment address"
            ) from err

        LOGGER.info(
            f"The address of the deployed contract {contract_id} is "
            f"{contract_address.to_bech32()}"
        )

        # register the new contract
        contract_data = InternalContractData(
            contract_id=contract_id,
            address=contract_address.to_bech32(),
            saved_values={},
            wasm_hash=get_file_hash(Path(self.wasm_path)),
            deploy_time=on_chain_tx.timestamp,
            last_upgrade_time=on_chain_tx.timestamp,
        )
        scenario_data.add_contract_data(contract_data)


@dataclass
class ContractUpgradeStep(TransactionStep):
    """
    Represents a smart contract upgrade
    """

    sender: str
    contract: str
    wasm_path: str
    gas_limit: int
    upgradeable: bool = True
    readable: bool = True
    payable: bool = False
    payable_by_sc: bool = False
    arguments: list = field(default_factory=lambda: [])
    abi_path: str | None = None

    def build_unsigned_transaction(self) -> Transaction:
        """
        Build the transaction for a contract upgrade

        :return: transaction built
        :rtype: Transaction
        """
        LOGGER.info(f"Upgrading contract {self.contract}")

        contract_designation = utils.retrieve_value_from_string(self.contract)
        contract_address = utils.get_address_instance(contract_designation)
        if self.abi_path is not None:
            abi = Abi.load(self.abi_path)
        else:
            abi = None

        retrieved_arguments = utils.retrieve_value_from_any(self.arguments)

        factory_config = TransactionsFactoryConfig(Config.get_config().get("CHAIN"))
        sc_factory = SmartContractTransactionsFactory(factory_config, abi=abi)
        bytecode = Path(self.wasm_path).read_bytes()

        return sc_factory.create_transaction_for_upgrade(
            sender=utils.get_address_instance(self.sender),
            contract=contract_address,
            bytecode=bytecode,
            arguments=retrieved_arguments,
            gas_limit=self.gas_limit,
            is_upgradeable=self.upgradeable,
            is_readable=self.readable,
            is_payable=self.payable,
            is_payable_by_sc=self.payable_by_sc,
        )

    def _post_transaction_execution(self, on_chain_tx: TransactionOnNetwork | None):
        """
        Save the new contract data in the Scenario

        :param on_chain_tx: successful upgrade transaction
        :type on_chain_tx: TransactionOnNetwork | None
        """
        if not isinstance(on_chain_tx, TransactionOnNetwork):
            raise ValueError("On chain transaction is None")
        contract = utils.retrieve_value_from_any(self.contract)
        scenario_data = ScenarioData.get()
        scenario_data.set_contract_abi_from_source(contract, Path(self.abi_path))

        try:
            scenario_data.set_contract_value(
                contract, "last_upgrade_time", on_chain_tx.timestamp
            )
        except errors.UnknownContract:  # any contract can be upgraded
            pass


@dataclass
class ResultsSaveKeys:
    master_key: str | None
    sub_keys: list[str | None] | None

    @staticmethod
    def from_input(data: Any) -> ResultsSaveKeys | None:
        """
        Parse the user input as an instance of this class

        :param data: input data for a yaml Scene file
        :type data: Any
        :return: results save keys if defined
        :rtype: ResultsSaveKeys | None
        """
        if data is None:
            return None
        if isinstance(data, str):
            return ResultsSaveKeys(data, None)
        if isinstance(data, list):
            for save_key in data:
                if not isinstance(save_key, str) and save_key is not None:
                    raise TypeError(f"Save keys must be a str or None, got {save_key}")
            return ResultsSaveKeys(None, data)
        if isinstance(data, dict):
            if len(data) != 1:
                raise ValueError(
                    "When providing a dict, only one root key should be provided"
                )
            master_key, sub_keys = list(data.items())[0]
            if not isinstance(master_key, str):
                raise TypeError("The root key should be a str")
            for save_key in sub_keys:
                if not isinstance(save_key, str) and save_key is not None:
                    raise TypeError(f"Save keys must be a str or None, got {save_key}")
            return ResultsSaveKeys(master_key, sub_keys)
        raise TypeError(f"ResultsSaveKeys can not parse the following input {data}")

    def parse_data_to_save(self, data: list) -> dict:
        """
        Parse data and break it into key-value pairs to save as data

        :param data: data to parse according the the results keys of this instance
        :type data: list
        :return: key-value pairs to save
        :rtype: dict
        """
        sub_keys = self.sub_keys
        if sub_keys is not None:
            if len(sub_keys) != len(data):
                raise ValueError(
                    f"Number of data parts ({len(data)} -> "
                    f"{data}) and save keys "
                    f"({len(sub_keys)} -> {sub_keys}) doesn't match"
                )
            to_save = dict(zip(sub_keys, data))
            if self.master_key is not None:
                to_save = {self.master_key: to_save}
        else:
            to_save = {self.master_key: data}
        return to_save


@dataclass
class ContractCallStep(TransactionStep):
    """
    Represents a smart contract endpoint call
    """

    contract: str
    endpoint: str
    gas_limit: int
    arguments: list = field(default_factory=list)
    value: int | str = 0
    esdt_transfers: list[EsdtTransfer] = field(default_factory=list)
    print_results: bool = False
    results_save_keys: ResultsSaveKeys | None = field(default=None)
    returned_data_parts: list | None = field(init=False, default=None)
    saved_results: dict = field(init=False, default_factory=dict)

    def build_unsigned_transaction(self) -> Transaction:
        """
        Build the transaction for a contract call

        :return: transaction built
        :rtype: Transaction
        """
        contract = utils.retrieve_value_from_any(self.contract)
        LOGGER.info(f"Calling {self.endpoint} for {contract} ")
        scenario_data = ScenarioData.get()

        retrieved_arguments = utils.retrieve_value_from_any(self.arguments)
        try:
            contract_abi = scenario_data.get_contract_abi(contract)
        except errors.UnknownAbiContract:
            contract_abi = None

        esdt_transfers = [
            TokenTransfer(
                Token(
                    utils.retrieve_value_from_string(trf.token_identifier),
                    utils.retrieve_value_from_any(trf.nonce),
                ),
                utils.retrieve_value_from_any(trf.amount),
            )
            for trf in self.esdt_transfers
        ]
        value = utils.retrieve_value_from_any(self.value)

        factory_config = TransactionsFactoryConfig(Config.get_config().get("CHAIN"))
        sc_factory = SmartContractTransactionsFactory(factory_config, abi=contract_abi)
        endpoint = utils.retrieve_value_from_string(self.endpoint)
        return sc_factory.create_transaction_for_execute(
            sender=utils.get_address_instance(self.sender),
            contract=utils.get_address_instance(contract),
            function=endpoint,
            arguments=retrieved_arguments,
            gas_limit=self.gas_limit,
            native_transfer_amount=value,
            token_transfers=esdt_transfers,
        )

    def _post_transaction_execution(self, on_chain_tx: TransactionOnNetwork | None):
        """
        Extract results of the smart contract call if it is successful

        :param on_chain_tx: successful transaction
        :type on_chain_tx: TransactionOnNetwork | None
        """
        scenario_data = ScenarioData.get()
        if self.results_save_keys is None:
            return

        contract = utils.retrieve_value_from_any(self.contract)
        scenario_data = ScenarioData.get()
        if not isinstance(on_chain_tx, TransactionOnNetwork):
            return
        if not on_chain_tx.status.is_successful:
            return
        try:
            contract_abi = scenario_data.get_contract_abi(contract)
        except errors.UnknownAbiContract:
            contract_abi = None
        parser = SmartContractTransactionsOutcomeParser(abi=contract_abi)
        endpoint = utils.retrieve_value_from_string(self.endpoint)
        outcome = parser.parse_execute(transaction=on_chain_tx, function=endpoint)
        self.returned_data_parts = convert_mx_data_to_vanilla(outcome.values)

        if self.returned_data_parts is None:
            raise ValueError("No data to save")
        to_save = self.results_save_keys.parse_data_to_save(self.returned_data_parts)
        for save_key, value in to_save.items():
            if save_key is not None:
                scenario_data.set_contract_value(contract, save_key, value)
                self.saved_results[save_key] = value

        if self.print_results:
            if self.saved_results is not None:
                print(json_dumps(self.saved_results))
            elif self.returned_data_parts is not None:
                print(json_dumps(self.returned_data_parts))

    def __post_init__(self):
        """
        After the initialisation of an instance, if the esdt transfers are
        found to be dict,
        will try to convert them to EsdtTransfers instances.
        Usefull for easy loading from yaml files
        """
        super().__post_init__()
        checked_transfers = []
        for trf in self.esdt_transfers:
            if isinstance(trf, EsdtTransfer):
                checked_transfers.append(trf)
            elif isinstance(trf, dict):
                checked_transfers.append(EsdtTransfer(**trf))
            else:
                raise ValueError(f"Unexpected type: {type(trf)}")
        self.esdt_transfers = checked_transfers

        if self.results_save_keys is not None and not isinstance(
            self.results_save_keys, ResultsSaveKeys
        ):
            self.results_save_keys = ResultsSaveKeys.from_input(self.results_save_keys)


@dataclass
class ContractQueryStep(Step):
    """
    Represents a smart contract query
    """

    contract: str
    endpoint: str
    arguments: list = field(default_factory=list)
    print_results: bool = False
    results_save_keys: ResultsSaveKeys | None = field(default=None)
    returned_data_parts: list | None = field(init=False, default=None)
    saved_results: dict = field(init=False, default_factory=dict)

    def __post_init__(self):
        """
        After the initialisation of an instance, if the esdt transfers are
        found to be dict,
        will try to convert them to EsdtTransfers instances.
        Usefull for easy loading from yaml files
        """
        if self.results_save_keys is not None and not isinstance(
            self.results_save_keys, ResultsSaveKeys
        ):
            self.results_save_keys = ResultsSaveKeys.from_input(self.results_save_keys)

    def save_results(self):
        """
        Save the results the query. This method replace the old way that was using
        expected_results
        """
        scenario_data = ScenarioData.get()
        if self.results_save_keys is None:
            return

        if self.returned_data_parts is None:
            raise ValueError("No data to save")

        LOGGER.info("Saving query results")

        self.saved_results = {}
        contract = utils.retrieve_value_from_any(self.contract)
        to_save = self.results_save_keys.parse_data_to_save(self.returned_data_parts)
        for save_key, value in to_save.items():
            if save_key is not None:
                scenario_data.set_contract_value(contract, save_key, value)
                self.saved_results[save_key] = value

    def execute(self):
        """
        Execute a query and optionally save the result
        """
        endpoint = utils.retrieve_value_from_any(self.endpoint)
        contract = utils.retrieve_value_from_any(self.contract)
        LOGGER.info(f"Query on {endpoint} for {contract}")
        scenario_data = ScenarioData.get()
        retrieved_arguments = utils.retrieve_value_from_any(self.arguments)
        try:
            contract_abi = scenario_data.get_contract_abi(contract)
        except errors.UnknownAbiContract:
            contract_abi = None

        sc_controller = SmartContractController(
            Config.get_config().get("CHAIN"), MyProxyNetworkProvider(), abi=contract_abi
        )
        returned_data_parts = sc_controller.query(
            contract=utils.get_address_instance(contract),
            function=endpoint,
            arguments=retrieved_arguments,
        )
        self.returned_data_parts = convert_mx_data_to_vanilla(returned_data_parts)

        self.save_results()

        if self.print_results:
            if self.saved_results is not None:
                print(json_dumps(self.saved_results))
            elif self.returned_data_parts is not None:
                print(json_dumps(self.returned_data_parts))

        LOGGER.info("Query successful")


@dataclass
class FuzzExecutionParameters:
    """
    Represents the parameters needed to excecute and check
    a test from a fuzz testing session
    """

    sender: str
    endpoint: str
    value: int = field(default=0)
    esdt_transfers: list[EsdtTransfer] = field(default_factory=list)
    arguments: list[Any] = field(default_factory=list)
    expected_outputs: list | None = field(
        default=None
    )  # TODO Replace with checks (success, transfers and results)
    description: str = field(default="")
    gas_limit: int | None = 0

    @staticmethod
    def from_dict(data: dict) -> FuzzExecutionParameters:
        """
        Instantiate this class from the raw data formed as a dictionnary

        :param data: data to parse
        :type data: dict
        :return: intance of this class
        :rtype: FuzzExecutionParameters
        """
        data_copy = data.copy()
        checked_transfers = []
        for trf in data.get("esdt_transfers", []):
            if isinstance(trf, EsdtTransfer):
                checked_transfers.append(trf)
            elif isinstance(trf, dict):
                checked_transfers.append(EsdtTransfer(**trf))
            else:
                raise ValueError(f"Unexpected type: {type(trf)}")
        data_copy["esdt_transfers"] = checked_transfers
        return FuzzExecutionParameters(**data_copy)


@dataclass
class FileFuzzerStep(Step):
    """
    Represents fuzzing tests where the inputs and expected outputs from each test
    are taken from a file
    """

    contract: str
    file_path: Path

    def __post_init__(self):
        """
        After the initialisation of an instance, if the esdt transfers are
        found to be dict,
        will try to convert them to EsdtTransfers instances.
        Usefull for easy loading from yaml files
        """
        self.file_path = Path(self.file_path)

    @classmethod
    def from_dict(cls, data: dict) -> Step:
        """
        Instantiate a Step instance from a dictionary

        :return: step instance
        :rtype: Step
        """
        return FileFuzzerStep(data["contract"], Path(data["file_path"]))

    def load_executions_parameters(self) -> list[FuzzExecutionParameters]:
        """
        Load the executions parameters for the fuzz tests as described by the file

        :return: executions parameters
        :rtype: list[FuzzExecutionParameters]
        """
        file_extension = self.file_path.suffix
        if file_extension in (".yaml", ".yml"):
            return self.load_executions_parameters_from_yaml()
        raise errors.WrongFuzzTestFile(
            f"Extension {file_extension} is not supported for file "
            f"{self.file_path.as_posix()}"
        )

    def load_executions_parameters_from_yaml(self) -> list[FuzzExecutionParameters]:
        """
        Load the executions parameters for the fuzz tests as described by the file,
        which is assumed to be a yaml file

        :return: executions parameters
        :rtype: list[FuzzExecutionParameters]
        """
        parameters = []
        with open(self.file_path.as_posix(), "r", encoding="utf-8") as file:
            raw_file = yaml.safe_load(file)
        try:
            raw_parameters = raw_file["parameters"]
        except KeyError as err:
            raise errors.WrongFuzzTestFile(
                "Fuzz Test file is missing the root key 'parameters'"
            ) from err

        for raw in raw_parameters:
            try:
                parameters.append(FuzzExecutionParameters.from_dict(raw))
            except (KeyError, IndexError) as err:
                raise errors.WrongFuzzTestFile(
                    "Wrong inputs for fuzz execution parameters"
                ) from err
        return parameters

    def execute(self):
        """
        Execute fuzz testing on the given contract using the parameters
        from the provided file
        """
        contract = utils.retrieve_value_from_any(self.contract)
        scenario_data = ScenarioData.get()
        try:
            contract_abi = scenario_data.get_contract_raw_abi(contract)
        except errors.UnknownAbiContract as err:
            raise errors.WrongFuzzTestFile(
                "ABI file must be provided for fuzz testing"
            ) from err
        LOGGER.info(f"Executing fuzz testing from file {self.file_path.as_posix()}")
        exec_parameters = self.load_executions_parameters()
        n_tests = len(exec_parameters)
        LOGGER.info(f"Found {n_tests} tests")
        for i, params in enumerate(exec_parameters):
            LOGGER.info(
                f"Executing fuzz test n°{i + 1}/{n_tests} ({i / n_tests:.0%}): "
                f"{params.description}"
            )
            self._execute_fuzz(contract_abi, params)

    def _execute_fuzz(
        self, contract_abi: dict, execution_parameters: FuzzExecutionParameters
    ):
        """
        Execute one instance of fuzz test

        :param contract_abi: raw abi for the contract, as a json
        :type contract_abi: dict
        :param execution_parameters: parameters of the test to execute
        :type execution_parameters: FuzzExecutionParameters
        """
        endpoint = None
        for e in contract_abi["endpoints"]:
            if e["name"] == execution_parameters.endpoint:
                endpoint = e
                break
        if endpoint is None:
            raise errors.WrongFuzzTestFile(
                f"Endpoint {execution_parameters.endpoint} not found in the contract "
                f"abi {contract_abi['name']}"
            )
        if endpoint.get("mutability", "mutable") == "readonly":
            self._execute_fuzz_query(execution_parameters)
        else:
            self._execute_fuzz_call(execution_parameters)

    def _execute_fuzz_query(self, execution_parameters: FuzzExecutionParameters):
        """
        Execute one instance of fuzz test that is considered as a query execution

        :param execution_parameters: parameters of the test to execute
        :type execution_parameters: FuzzExecutionParameters
        """
        contract = utils.retrieve_value_from_any(self.contract)
        save_key = "fuzz_test_query_results"
        query_step = ContractQueryStep(
            contract,
            execution_parameters.endpoint,
            arguments=execution_parameters.arguments,
            results_save_keys=save_key,
        )
        query_step.execute()
        scenario_data = ScenarioData.get()
        results = scenario_data.get_contract_value(contract, save_key)
        if results != execution_parameters.expected_outputs:
            raise errors.FuzzTestFailed(
                f"Outputs are different from expected: found {results} but wanted "
                f"{execution_parameters.expected_outputs}"
            )

    def _execute_fuzz_call(self, execution_parameters: FuzzExecutionParameters):
        """
        Execute one instance of fuzz test that is considered as a query execution

        :param execution_parameters: parameters of the test to execute
        :type execution_parameters: FuzzExecutionParameters
        """
        contract = utils.retrieve_value_from_any(self.contract)
        save_key = "fuzz_test_call_results"
        call_step = ContractCallStep(
            contract=contract,
            endpoint=execution_parameters.endpoint,
            gas_limit=execution_parameters.gas_limit,
            arguments=execution_parameters.arguments,
            value=execution_parameters.value,
            esdt_transfers=execution_parameters.esdt_transfers,
            sender=execution_parameters.sender,
            results_save_keys=save_key,
        )
        call_step.execute()
        if execution_parameters.expected_outputs is not None:
            scenario_data = ScenarioData.get()
            results = scenario_data.get_contract_value(contract, save_key)
            if results != execution_parameters.expected_outputs:
                raise errors.FuzzTestFailed(
                    f"Outputs are different from expected: found {results} but wanted "
                    f"{execution_parameters.expected_outputs}"
                )


@dataclass
class FungibleIssueStep(TransactionStep):
    """
    Represents the issuance of a fungible token
    """

    token_name: str
    token_ticker: str
    initial_supply: int
    num_decimals: int
    can_freeze: bool = False
    can_wipe: bool = False
    can_pause: bool = False
    can_change_owner: bool = False
    can_upgrade: bool = False
    can_add_special_roles: bool = False

    def build_unsigned_transaction(self) -> Transaction:
        """
        Build the transaction to issue a fungible token

        :return: transaction built
        :rtype: Transaction
        """
        sender = utils.get_address_instance(self.sender)
        token_name = utils.retrieve_value_from_any(self.token_name)
        token_ticker = utils.retrieve_value_from_any(self.token_ticker)
        initial_supply = utils.retrieve_value_from_any(self.initial_supply)
        LOGGER.info(
            f"Issuing fungible token named {token_name} "
            f"for the account {self.sender} ({sender.bech32()})"
        )
        factory_config = TransactionsFactoryConfig(Config.get_config().get("CHAIN"))
        tx_factory = TokenManagementTransactionsFactory(factory_config)

        return tx_factory.create_transaction_for_issuing_fungible(
            sender=sender,
            token_name=token_name,
            token_ticker=token_ticker,
            initial_supply=initial_supply,
            num_decimals=self.num_decimals,
            can_freeze=self.can_freeze,
            can_wipe=self.can_wipe,
            can_pause=self.can_pause,
            can_change_owner=self.can_change_owner,
            can_upgrade=self.can_upgrade,
            can_add_special_roles=self.can_add_special_roles,
        )

    def _post_transaction_execution(self, on_chain_tx: TransactionOnNetwork | None):
        """
        Extract the newly issued token identifier and save it within the Scenario

        :param on_chain_tx: successful transaction
        :type on_chain_tx: TransactionOnNetwork | None
        """
        if not isinstance(on_chain_tx, TransactionOnNetwork):
            raise ValueError("On chain transaction is None")
        parsed_outcome = (
            TokenManagementTransactionsOutcomeParser().parse_issue_fungible(on_chain_tx)
        )
        token_identifier = parsed_outcome[0].token_identifier
        scenario_data = ScenarioData.get()
        LOGGER.info(f"Newly issued token got the identifier {token_identifier}")
        token_name = utils.retrieve_value_from_any(self.token_name)
        token_ticker = utils.retrieve_value_from_any(self.token_ticker)
        scenario_data.add_token_data(
            TokenData(
                name=token_name,
                ticker=token_ticker,
                identifier=token_identifier,
                saved_values={},
                type=TokenTypeEnum.FUNGIBLE,
            )
        )


@dataclass
class NonFungibleIssueStep(TransactionStep):
    """
    Represents the issuance of a non fungible token
    """

    token_name: str
    token_ticker: str
    can_freeze: bool = False
    can_wipe: bool = False
    can_pause: bool = False
    can_change_owner: bool = False
    can_upgrade: bool = False
    can_add_special_roles: bool = False
    can_transfer_nft_create_role: bool = False

    def build_unsigned_transaction(self) -> Transaction:
        """
        Build the transaction to issue a non fungible token

        :return: transaction built
        :rtype: Transaction
        """
        sender = utils.get_address_instance(self.sender)
        token_name = utils.retrieve_value_from_any(self.token_name)
        token_ticker = utils.retrieve_value_from_any(self.token_ticker)
        LOGGER.info(
            f"Issuing non fungible token named {token_name} "
            f"for the account {self.sender} ({sender.bech32()})"
        )
        factory_config = TransactionsFactoryConfig(Config.get_config().get("CHAIN"))
        tx_factory = TokenManagementTransactionsFactory(factory_config)
        return tx_factory.create_transaction_for_issuing_non_fungible(
            sender=sender,
            token_name=token_name,
            token_ticker=token_ticker,
            can_freeze=self.can_freeze,
            can_wipe=self.can_wipe,
            can_pause=self.can_pause,
            can_transfer_nft_create_role=self.can_transfer_nft_create_role,
            can_change_owner=self.can_change_owner,
            can_upgrade=self.can_upgrade,
            can_add_special_roles=self.can_add_special_roles,
        )

    def _post_transaction_execution(self, on_chain_tx: TransactionOnNetwork | None):
        """
        Extract the newly issued token identifier and save it within the Scenario

        :param on_chain_tx: successful transaction
        :type on_chain_tx: TransactionOnNetwork | None
        """
        if not isinstance(on_chain_tx, TransactionOnNetwork):
            raise ValueError("On chain transaction is None")
        parsed_outcome = (
            TokenManagementTransactionsOutcomeParser().parse_issue_non_fungible(
                on_chain_tx
            )
        )
        token_identifier = parsed_outcome[0].token_identifier
        scenario_data = ScenarioData.get()
        LOGGER.info(f"Newly issued token got the identifier {token_identifier}")
        token_name = utils.retrieve_value_from_any(self.token_name)
        token_ticker = utils.retrieve_value_from_any(self.token_ticker)
        scenario_data.add_token_data(
            TokenData(
                name=token_name,
                ticker=token_ticker,
                identifier=token_identifier,
                saved_values={},
                type=TokenTypeEnum.NON_FUNGIBLE,
            )
        )


@dataclass
class SemiFungibleIssueStep(TransactionStep):
    """
    Represents the issuance of a semi fungible token
    """

    token_name: str
    token_ticker: str
    can_freeze: bool = False
    can_wipe: bool = False
    can_pause: bool = False
    can_change_owner: bool = False
    can_upgrade: bool = False
    can_add_special_roles: bool = False
    can_transfer_nft_create_role: bool = False

    def build_unsigned_transaction(self) -> Transaction:
        """
        Build the transaction to issue a semi fungible token

        :return: transaction built
        :rtype: Transaction
        """
        sender = utils.get_address_instance(self.sender)
        token_name = utils.retrieve_value_from_any(self.token_name)
        token_ticker = utils.retrieve_value_from_any(self.token_ticker)
        LOGGER.info(
            f"Issuing semi fungible token named {token_name} "
            f"for the account {self.sender} ({sender.bech32()})"
        )
        factory_config = TransactionsFactoryConfig(Config.get_config().get("CHAIN"))
        tx_factory = TokenManagementTransactionsFactory(factory_config)
        return tx_factory.create_transaction_for_issuing_semi_fungible(
            sender=sender,
            token_name=token_name,
            token_ticker=token_ticker,
            can_freeze=self.can_freeze,
            can_transfer_nft_create_role=self.can_transfer_nft_create_role,
            can_wipe=self.can_wipe,
            can_pause=self.can_pause,
            can_change_owner=self.can_change_owner,
            can_upgrade=self.can_upgrade,
            can_add_special_roles=self.can_add_special_roles,
        )

    def _post_transaction_execution(self, on_chain_tx: TransactionOnNetwork | None):
        """
        Extract the newly issued token identifier and save it within the Scenario

        :param on_chain_tx: successful transaction
        :type on_chain_tx: TransactionOnNetwork | None
        """
        if not isinstance(on_chain_tx, TransactionOnNetwork):
            raise ValueError("On chain transaction is None")
        parsed_outcome = (
            TokenManagementTransactionsOutcomeParser().parse_issue_semi_fungible(
                on_chain_tx
            )
        )
        token_identifier = parsed_outcome[0].token_identifier
        scenario_data = ScenarioData.get()
        LOGGER.info(f"Newly issued token got the identifier {token_identifier}")
        token_name = utils.retrieve_value_from_any(self.token_name)
        token_ticker = utils.retrieve_value_from_any(self.token_ticker)
        scenario_data.add_token_data(
            TokenData(
                name=token_name,
                ticker=token_ticker,
                identifier=token_identifier,
                saved_values={},
                type=TokenTypeEnum.SEMI_FUNGIBLE,
            )
        )


@dataclass
class MetaIssueStep(TransactionStep):
    """
    Represents the issuance of a meta fungible token
    """

    token_name: str
    token_ticker: str
    num_decimals: int
    can_freeze: bool = False
    can_wipe: bool = False
    can_pause: bool = False
    can_change_owner: bool = False
    can_upgrade: bool = False
    can_add_special_roles: bool = False
    can_transfer_nft_create_role: bool = False

    def build_unsigned_transaction(self) -> Transaction:
        """
        Build the transaction to issue a meta token

        :return: transaction built
        :rtype: Transaction
        """
        sender = utils.get_address_instance(self.sender)
        token_name = utils.retrieve_value_from_any(self.token_name)
        token_ticker = utils.retrieve_value_from_any(self.token_ticker)
        LOGGER.info(
            f"Issuing meta token named {token_name} "
            f"for the account {self.sender} ({sender.bech32()})"
        )
        factory_config = TransactionsFactoryConfig(Config.get_config().get("CHAIN"))
        tx_factory = TokenManagementTransactionsFactory(factory_config)
        return tx_factory.create_transaction_for_registering_meta_esdt(
            sender=sender,
            token_name=token_name,
            token_ticker=token_ticker,
            num_decimals=self.num_decimals,
            can_freeze=self.can_freeze,
            can_wipe=self.can_wipe,
            can_pause=self.can_pause,
            can_transfer_nft_create_role=self.can_transfer_nft_create_role,
            can_change_owner=self.can_change_owner,
            can_upgrade=self.can_upgrade,
            can_add_special_roles=self.can_add_special_roles,
        )

    def _post_transaction_execution(self, on_chain_tx: TransactionOnNetwork | None):
        """
        Extract the newly issued token identifier and save it within the Scenario

        :param on_chain_tx: successful transaction
        :type on_chain_tx: TransactionOnNetwork | None
        """
        if not isinstance(on_chain_tx, TransactionOnNetwork):
            raise ValueError("On chain transaction is None")
        parsed_outcome = (
            TokenManagementTransactionsOutcomeParser().parse_register_meta_esdt(
                on_chain_tx
            )
        )
        token_identifier = parsed_outcome[0].token_identifier
        scenario_data = ScenarioData.get()
        LOGGER.info(f"Newly issued token got the identifier {token_identifier}")
        token_name = utils.retrieve_value_from_any(self.token_name)
        token_ticker = utils.retrieve_value_from_any(self.token_ticker)
        scenario_data.add_token_data(
            TokenData(
                name=token_name,
                ticker=token_ticker,
                identifier=token_identifier,
                saved_values={},
                type=TokenTypeEnum.META,
            )
        )


@dataclass
class ManageTokenRolesStep(TransactionStep):
    """
    A base step to set or unset roles on a token.
    Can not be used on its own: on must use the child classes
    """

    is_set: bool
    token_identifier: str
    target: str
    roles: list[str]
    ALLOWED_ROLES: ClassVar[set] = set()

    def __post_init__(self):
        super().__post_init__()
        for role in self.roles:
            if role not in self.ALLOWED_ROLES:
                raise ValueError(
                    f"role {role} is not in allowed roles {self.ALLOWED_ROLES}"
                )

    def construct_role_kwargs(self, include_missing: bool = False) -> dict[str, bool]:
        """
        construct the role kwargs needed by the factory to construct
        the tx depending on which role to set or unset

        :param include_missing: also return missing roles as False
        :type include_missing: bool
        :return: kwargs to pass to the tx factory
        :rtype: dict[str, bool]
        """
        prefix = "add_role_" if self.is_set else "remove_role_"
        roles = {prefix + r: True for r in self.roles}
        if include_missing:
            for role in self.ALLOWED_ROLES:
                role_action = prefix + role
                if role_action not in roles:
                    roles[role_action] = False
        return roles


@dataclass
class ManageFungibleTokenRolesStep(ManageTokenRolesStep):
    """
    This step is used to set or unset roles for an adress on a fungible token
    """

    ALLOWED_ROLES: ClassVar[set] = {
        "local_mint",
        "local_burn",
        "esdt_transfer_role",
    }

    def build_unsigned_transaction(self) -> Transaction:
        """
        Build the transaction to set roles on a fungible token

        :return: transaction built
        :rtype: Transaction
        """
        sender = utils.get_address_instance(self.sender)
        token_identifier = utils.retrieve_value_from_string(self.token_identifier)
        target = utils.get_address_instance(self.target)
        LOGGER.info(
            f"Setting roles {self.roles} on the token {self.token_identifier}"
            f" ({token_identifier}) for {self.target} ({target.bech32()})"
        )

        factory_config = TransactionsFactoryConfig(Config.get_config().get("CHAIN"))
        tx_factory = TokenManagementTransactionsFactory(factory_config)

        role_kwargs = self.construct_role_kwargs(include_missing=True)

        if self.is_set:
            return tx_factory.create_transaction_for_setting_special_role_on_fungible_token(  # noqa: E501
                sender=sender,
                user=target,
                token_identifier=token_identifier,
                **role_kwargs,
            )
        return (
            tx_factory.create_transaction_for_unsetting_special_role_on_fungible_token(  # noqa: E501
                sender=sender,
                user=target,
                token_identifier=token_identifier,
                **role_kwargs,
            )
        )


@dataclass
class ManageNonFungibleTokenRolesStep(ManageTokenRolesStep):
    """
    This step is used to set or unset roles for an adress on a non fungible token
    """

    ALLOWED_ROLES: ClassVar[set] = {
        "nft_create",
        "nft_burn",
        "nft_update_attributes",
        "nft_add_uri",
        "esdt_transfer_role",
        "nft_update",
        "esdt_modify_royalties",
        "esdt_set_new_uri",
        "esdt_modify_creator",
        "nft_recreate",
    }

    def build_unsigned_transaction(self) -> Transaction:
        """
        Build the transaction to set roles on a non fungible token

        :return: transaction built
        :rtype: Transaction
        """
        sender = utils.get_address_instance(self.sender)
        token_identifier = utils.retrieve_value_from_string(self.token_identifier)
        target = utils.get_address_instance(self.target)
        LOGGER.info(
            f"Setting roles {self.roles} on the token {self.token_identifier}"
            f" ({token_identifier}) for {self.target} ({target.bech32()})"
        )

        factory_config = TransactionsFactoryConfig(Config.get_config().get("CHAIN"))
        tx_factory = TokenManagementTransactionsFactory(factory_config)

        role_kwargs = self.construct_role_kwargs()
        if self.is_set:
            return tx_factory.create_transaction_for_setting_special_role_on_non_fungible_token(  # noqa: E501
                sender=sender,
                user=target,
                token_identifier=token_identifier,
                **role_kwargs,
            )
        return tx_factory.create_transaction_for_unsetting_special_role_on_non_fungible_token(  # noqa: E501
            sender=sender, user=target, token_identifier=token_identifier, **role_kwargs
        )


@dataclass
class ManageSemiFungibleTokenRolesStep(ManageTokenRolesStep):
    """
    This step is used to set or unset roles for an adress on a semi fungible token
    """

    ALLOWED_ROLES: ClassVar[set] = {
        "nft_create",
        "nft_burn",
        "nft_add_quantity",
        "esdt_transfer_role",
        "nft_update",
        "esdt_modify_royalties",
        "esdt_set_new_uri",
        "esdt_modify_creator",
        "nft_recreate",
    }

    def build_unsigned_transaction(self) -> Transaction:
        """
        Build the transaction to set roles on a non fungible token

        :return: transaction built
        :rtype: Transaction
        """
        sender = utils.get_address_instance(self.sender)
        token_identifier = utils.retrieve_value_from_string(self.token_identifier)
        target = utils.get_address_instance(self.target)
        LOGGER.info(
            f"Setting roles {self.roles} on the token {self.token_identifier}"
            f" ({token_identifier}) for {self.target} ({target.bech32()})"
        )

        factory_config = TransactionsFactoryConfig(Config.get_config().get("CHAIN"))
        tx_factory = TokenManagementTransactionsFactory(factory_config)

        role_kwargs = self.construct_role_kwargs()
        if self.is_set:
            return tx_factory.create_transaction_for_setting_special_role_on_semi_fungible_token(  # noqa: E501
                sender=sender,
                user=target,
                token_identifier=token_identifier,
                **role_kwargs,
            )
        return tx_factory.create_transaction_for_unsetting_special_role_on_semi_fungible_token(  # noqa: E501
            sender=sender, user=target, token_identifier=token_identifier, **role_kwargs
        )


@dataclass
class ManageMetaTokenRolesStep(ManageSemiFungibleTokenRolesStep):
    """
    This step is used to set or unset roles for an adress on a meta token
    """


@dataclass
class FungibleMintStep(TransactionStep):
    """
    This step is used to mint an additional supply for an already
    existing fungible token
    """

    token_identifier: str
    amount: str | int

    def build_unsigned_transaction(self) -> Transaction:
        """
        Build the transaction to mint a fungible token

        :return: transaction built
        :rtype: Transaction
        """
        sender = utils.get_address_instance(self.sender)
        token_identifier = utils.retrieve_value_from_string(self.token_identifier)
        amount = utils.retrieve_value_from_any(self.amount)
        LOGGER.info(
            f"Minting additional supply of {amount} ({self.amount}) for the token "
            f" {token_identifier} ({self.token_identifier})"
        )
        factory_config = TransactionsFactoryConfig(Config.get_config().get("CHAIN"))
        tx_factory = TokenManagementTransactionsFactory(factory_config)
        return tx_factory.create_transaction_for_local_minting(
            sender=sender, token_identifier=token_identifier, supply_to_mint=amount
        )


@dataclass
class NonFungibleMintStep(TransactionStep):
    """
    This step is used to mint a new nonce for an already existing non fungible token.
    It can be used for NFTs, SFTs and Meta tokens.
    """

    token_identifier: str
    amount: str | int
    name: str = ""
    royalties: str | int = 0
    hash: str = ""
    attributes: str = ""
    uris: list[str] = field(default_factory=lambda: [])

    def build_unsigned_transaction(self) -> Transaction:
        """
        Build the transaction to mint a fungible token

        :return: transaction built
        :rtype: Transaction
        """
        sender = utils.get_address_instance(self.sender)
        token_identifier = utils.retrieve_value_from_string(self.token_identifier)
        amount = utils.retrieve_value_from_any(self.amount)
        LOGGER.info(
            f"Minting new nonce with a supply of {amount} ({self.amount}) for the token"
            f" {token_identifier} ({self.token_identifier})"
        )

        factory_config = TransactionsFactoryConfig(Config.get_config().get("CHAIN"))
        tx_factory = TokenManagementTransactionsFactory(factory_config)
        return tx_factory.create_transaction_for_creating_nft(
            sender=sender,
            token_identifier=token_identifier,
            initial_quantity=amount,
            name=utils.retrieve_value_from_string(self.name),
            royalties=utils.retrieve_value_from_any(self.royalties),
            hash=utils.retrieve_value_from_string(self.hash),
            attributes=bytes(
                utils.retrieve_value_from_string(self.attributes), "utf-8"
            ),
            uris=utils.retrieve_values_from_strings(self.uris),
        )

    def _post_transaction_execution(self, on_chain_tx: TransactionOnNetwork | None):
        """
        Extract the newly issued nonce and print it

        :param on_chain_tx: successful transaction
        :type on_chain_tx: TransactionOnNetwork | None
        """
        if not isinstance(on_chain_tx, TransactionOnNetwork):
            return
        parsed_outcome = TokenManagementTransactionsOutcomeParser().parse_nft_create(
            on_chain_tx
        )
        new_nonce = parsed_outcome[0].nonce
        LOGGER.info(f"Newly issued nonce is {new_nonce}")


@dataclass
class EgldTransferStep(TransactionStep):
    """
    This step is used to transfer some eGLD to an address
    """

    receiver: str
    amount: str | int

    def build_unsigned_transaction(self) -> Transaction:
        """
        Build the transaction for an egld transfer

        :return: transaction built
        :rtype: Transaction
        """
        amount = int(utils.retrieve_value_from_any(self.amount))
        sender = utils.get_address_instance(self.sender)
        receiver = utils.get_address_instance(self.receiver)

        LOGGER.info(
            f"Sending {amount} eGLD from {self.sender} ({sender.bech32()}) to "
            f"{self.receiver} ({receiver.bech32()})"
        )
        factory_config = TransactionsFactoryConfig(Config.get_config().get("CHAIN"))
        tr_factory = TransferTransactionsFactory(factory_config)
        return tr_factory.create_transaction_for_native_token_transfer(
            sender=sender,
            receiver=receiver,
            native_amount=amount,
        )


@dataclass
class FungibleTransferStep(TransactionStep):
    """
    This step is used to transfer some fungible ESDT to an address
    """

    receiver: str
    token_identifier: str
    amount: str | int

    def build_unsigned_transaction(self) -> Transaction:
        """
        Build the transaction for an ESDT transfer

        :return: transaction built
        :rtype: Transaction
        """
        token_identifier = utils.retrieve_value_from_string(self.token_identifier)
        amount = int(utils.retrieve_value_from_any(self.amount))
        sender = utils.get_address_instance(self.sender)
        receiver = utils.get_address_instance(self.receiver)

        esdt_transfers = [TokenTransfer(Token(token_identifier, 0), amount)]

        LOGGER.info(
            f"Sending {amount} {token_identifier} from {self.sender} "
            f"({sender.bech32()}) to {self.receiver} ({receiver.bech32()})"
        )
        factory_config = TransactionsFactoryConfig(Config.get_config().get("CHAIN"))
        tr_factory = TransferTransactionsFactory(factory_config)
        return tr_factory.create_transaction_for_esdt_token_transfer(
            sender=sender,
            receiver=receiver,
            token_transfers=esdt_transfers,
        )


@dataclass
class NonFungibleTransferStep(TransactionStep):
    """
    This step is used to transfer some non fungible ESDT to an address
    """

    receiver: str
    token_identifier: str
    nonce: str | int
    amount: str | int

    def build_unsigned_transaction(self) -> Transaction:
        """
        Build the transaction for a non fungible transfer

        :return: transaction built
        :rtype: Transaction
        """
        token_identifier = utils.retrieve_value_from_string(self.token_identifier)
        nonce = int(utils.retrieve_value_from_any(self.nonce))
        amount = int(utils.retrieve_value_from_any(self.amount))
        sender = utils.get_address_instance(self.sender)
        receiver = utils.get_address_instance(self.receiver)
        serializer = Serializer("@")
        nonce_as_str = serializer.serialize([U64Value(nonce)])
        esdt_transfers = [TokenTransfer(Token(token_identifier, nonce), amount)]

        LOGGER.info(
            f"Sending {amount} {token_identifier}-{nonce_as_str} from "
            f"{self.sender} ({sender.bech32()}) to {self.receiver} "
            f"({receiver.bech32()})"
        )
        factory_config = TransactionsFactoryConfig(Config.get_config().get("CHAIN"))
        tr_factory = TransferTransactionsFactory(factory_config)
        return tr_factory.create_transaction_for_esdt_token_transfer(
            sender=sender,
            receiver=receiver,
            token_transfers=esdt_transfers,
        )


@dataclass
class MultiTransfersStep(TransactionStep):
    """
    This step is used to transfer multiple ESDTs to an address
    """

    receiver: str
    transfers: list[EsdtTransfer]

    def __post_init__(self):
        """
        After the initialisation of an instance, if the esdt transfers are
        found to be dict,
        will try to convert them to EsdtTransfers instances.
        Usefull for easy loading from yaml files
        """
        super().__post_init__()
        checked_transfers = []
        for trf in self.transfers:
            if isinstance(trf, EsdtTransfer):
                checked_transfers.append(trf)
            elif isinstance(trf, dict):
                checked_transfers.append(EsdtTransfer(**trf))
            else:
                raise ValueError(f"Unexpected type: {type(trf)}")
        self.transfers = checked_transfers

    def build_unsigned_transaction(self) -> Transaction:
        """
        Build the transaction for multiple transfers

        :return: transaction built
        :rtype: Transaction
        """
        sender = utils.get_address_instance(self.sender)
        receiver = utils.get_address_instance(self.receiver)
        esdt_transfers = []
        esdt_transfers_strs = []
        serializer = Serializer("@")
        for trf in self.transfers:
            token_identifier = utils.retrieve_value_from_string(trf.token_identifier)
            amount = int(utils.retrieve_value_from_any(trf.amount))
            nonce = int(utils.retrieve_value_from_any(trf.nonce))
            nonce_as_str = serializer.serialize([U64Value(nonce)])
            esdt_transfers.append(TokenTransfer(Token(token_identifier, nonce), amount))
            esdt_transfers_strs.append(f"{amount} {token_identifier}-{nonce_as_str}")

        LOGGER.info(
            f"Sending {', '.join(esdt_transfers_strs)} from {self.sender} "
            f"({sender.bech32()}) to {self.receiver} ({receiver.bech32()})"
        )
        factory_config = TransactionsFactoryConfig(Config.get_config().get("CHAIN"))
        tr_factory = TransferTransactionsFactory(factory_config)
        return tr_factory.create_transaction_for_esdt_token_transfer(
            sender=sender,
            receiver=receiver,
            token_transfers=esdt_transfers,
        )


@dataclass
class PythonStep(Step):
    """
    This Step execute a custom python function of the user
    """

    module_path: str
    function: str
    arguments: list = field(default_factory=list)
    keyword_arguments: dict = field(default_factory=dict)
    print_result: bool = True
    result_save_key: str | None = None

    def execute(self):
        """
        Execute the specified function
        """
        module_path = Path(self.module_path)
        module_name = module_path.stem
        LOGGER.info(
            f"Executing python function {self.function} from user module {module_name}"
        )

        # load module and function
        spec = spec_from_file_location(module_name, module_path.as_posix())
        user_module = module_from_spec(spec)
        spec.loader.exec_module(user_module)
        function = utils.retrieve_value_from_string(self.function)
        user_function = getattr(user_module, function)

        # transform args and kwargs and execute
        retrieved_arguments = utils.retrieve_value_from_any(self.arguments)
        retrieved_keyword_arguments = utils.retrieve_value_from_any(
            self.keyword_arguments
        )
        result = user_function(*retrieved_arguments, **retrieved_keyword_arguments)

        if self.result_save_key is not None:
            if self.print_result:
                LOGGER.info(
                    f"Function result: {result}, saved at {self.result_save_key}"
                )

            scenario_data = ScenarioData.get()
            scenario_data.set_value(self.result_save_key, result)


@dataclass
class SceneStep(Step):
    """
    This Step does nothing asside holding a variable
    with the path of the scene. The actual action is operated at the `Scene` level.
    """

    scene_path: str

    def execute(self):
        """
        Does nothing and should not be called. It is still implemented to avoid the
        warning W0622.
        """
        LOGGER.warning("The execute function of a SceneStep was called")


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
            step_class_object = getattr(sys.modules[__name__], step_class_name)
        except AttributeError as err:
            raise errors.UnkownStep(step_type) from err
        if not issubclass(step_class_object, Step):
            raise errors.UnkownStep(step_type)
        try:
            step = step_class_object(**raw_step)
        except Exception as err:
            raise errors.InvalidStepDefinition(step_type, raw_step) from err
        steps_list.append(step)
    return steps_list


@dataclass
class SetVarsStep(Step):
    """
    Represents a step to set variables within the Scenario
    """

    variables: dict[str, Any]

    def execute(self):
        """
        Parse the values to be assigned to the given variables
        """
        scenario_data = ScenarioData.get()

        for raw_key, raw_value in self.variables.items():
            key = utils.retrieve_value_from_string(raw_key)
            value = utils.retrieve_value_from_any(raw_value)
            LOGGER.info(
                f"Setting variable `{key}` ({raw_key}) with the value "
                f"`{value}` ({raw_value})"
            )
            scenario_data.set_value(key, value)


@dataclass
class GenerateWalletsStep(Step):
    """
    Represents a step to generate some MultiversX wallets
    For now, only pem wallets are supported
    """

    save_folder: Path
    wallets: int | list[str]
    shard: int | None = field(default=None)

    def __post_init__(self):
        self.save_folder = Path(self.save_folder)

    def execute(self):
        """
        Create the wanted wallets at the designated location

        """
        if isinstance(self.wallets, int):
            n_wallets = self.wallets
            names = [None] * n_wallets
        elif isinstance(self.wallets, list):
            n_wallets = len(self.wallets)
            names = self.wallets
        else:
            raise ValueError(
                "the wallets argument must be of type int or list[str], "
                f"got {type(self.wallets)}"
            )
        for i, name in enumerate(names):
            pem_wallet, wallet_address = generate_pem_wallet(self.shard)
            if name is None:
                wallet_name = wallet_address.to_bech32()
            else:
                wallet_name = utils.retrieve_value_from_string(name)
            wallet_path = self.save_folder / f"{wallet_name}.pem"
            if os.path.isfile(wallet_path.as_posix()):
                raise errors.WalletAlreadyExist(wallet_path)
            pem_wallet.save(wallet_path)
            LOGGER.info(
                f"Wallet n°{i + 1}/{n_wallets} generated with address "
                f"{wallet_address.to_bech32()} at {wallet_path}"
            )


@dataclass
class R3D4FaucetStep(Step):
    """
    Represents a step to request some EGLD from the r3d4 faucet
    """

    targets: list[str] | str
    ALLOWED_NETWORKS: ClassVar[set] = (NetworkEnum.DEV, NetworkEnum.TEST)

    def get_egld_details(self) -> dict:
        """
        Request r3d4 for the details regarding the EGLD token faucet

        :return: token id, max amount and available
        :rtype: Tuple[int, int]
        """
        config = Config.get_config()
        url = f"{config.get('R3D4_API')}/faucet/tokens"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        chain = config.get("CHAIN")
        for token_data in data:
            if token_data["network"] != chain:
                continue
            if token_data["identifier"] in ("xEGLD", "dEGLD", "EGLD", "tEGLD"):
                return token_data
        raise errors.TokenNotFound("Could not found EGLD in the faucet")

    def execute(self):
        """
        Seach for the r3d4 token id of EGLD in the current network and
        ask for EGLD from the faucet
        """
        scenario_data = ScenarioData.get()
        if scenario_data.network not in self.ALLOWED_NETWORKS:
            raise errors.WrongNetworkForStep(
                scenario_data.network, self.ALLOWED_NETWORKS
            )
        egld_details = self.get_egld_details()
        request_amount = float(egld_details["max"])
        targets = utils.retrieve_value_from_any(self.targets)
        for target in targets:
            address = utils.get_address_instance(target)
            LOGGER.info(
                f"Requesting {request_amount} {egld_details['identifier']}"
                f" from r3d4 faucet for {target} ({address.to_bech32()})"
            )
            self.request_faucet(
                address.to_bech32(), egld_details["id"], str(request_amount)
            )

    def request_faucet(self, bech32: str, token_id: str, amount: str):
        """
        Request the faucet for a token amount for an address

        :param bech32: address where to receive the tokens
        :type bech32: str
        :param token_id: r3d4 token id to recieve
        :type token_id: int
        :param amount: amount of token to recieve, with decimal
        :type amount: str
        """
        config = Config.get_config()
        url = f"{config.get('R3D4_API')}/faucet/list"
        headers = {
            "accept": "application/json",
        }
        data = {
            "formdata": {
                "network": config.get("CHAIN"),
                "token": token_id,
                "address": bech32,
                "amount": amount,
            }
        }
        response = requests.post(url, json=data, headers=headers, timeout=5)
        response.raise_for_status()
        return_data = response.json()
        if "error" in return_data:
            raise errors.FaucetFailed(return_data["error"])
        LOGGER.info(f"Response from faucet: {return_data['success']}")


@dataclass
class ChainSimulatorFaucetStep(Step):
    """
    Represents a step to request some EGLD from the chain-simulator faucet
    (aka initial wallets of the chain simulator)
    """

    targets: list[str] | str
    amount: int
    ALLOWED_NETWORKS: ClassVar[set] = (NetworkEnum.CHAIN_SIMULATOR,)

    def execute(self):
        """
        Seach for the r3d4 token id of EGLD in the current network and
        ask for EGLD from the faucet
        """
        scenario_data = ScenarioData.get()
        if scenario_data.network not in self.ALLOWED_NETWORKS:
            raise errors.WrongNetworkForStep(
                scenario_data.network, self.ALLOWED_NETWORKS
            )
        proxy = MyProxyNetworkProvider()
        initial_wallet_data = proxy.get_initial_wallets()
        sender = initial_wallet_data["balanceWallets"]["0"]["address"]["bech32"]
        sender_nonce = proxy.get_account(Address.new_from_bech32(sender)).nonce
        targets = utils.retrieve_value_from_any(self.targets)
        for target in targets:
            egld_step = EgldTransferStep(
                sender=sender, receiver=target, amount=self.amount
            )
            tx = egld_step.build_unsigned_transaction()
            tx.signature = b"aa"
            tx.nonce = sender_nonce
            on_chain_tx = send_and_wait_for_result(tx)
            SuccessCheck().raise_on_failure(on_chain_tx)
            LOGGER.info(
                f"Transaction successful: {get_tx_link(on_chain_tx.hash.hex())}"
            )
            sender_nonce += 1


@dataclass
class WaitStep(Step):
    """
    Represent a step to wait until a condition is fulfilled
    """

    for_seconds: Any | None = field(default=None)
    for_blocks: Any | None = field(default=None)
    shard: Any | None = field(default=METACHAIN_ID)

    def execute(self):
        """
        Wait until the specified condition is met
        """
        for_seconds = utils.retrieve_value_from_any(self.for_seconds)
        for_blocks = utils.retrieve_value_from_any(self.for_blocks)
        if for_seconds is not None:
            LOGGER.info(f"Waiting for {for_seconds} seconds")
            time.sleep(for_seconds)
            return
        if for_blocks is not None:
            network = Config.get_config().get_network()
            shard = utils.retrieve_value_from_any(self.shard)
            LOGGER.info(f"Waiting for {for_blocks} blocks on shard {shard}")
            if network == NetworkEnum.CHAIN_SIMULATOR:
                MyProxyNetworkProvider().generate_blocks(for_blocks)
            else:
                utils.wait_for_n_blocks(shard, for_blocks)
        else:
            raise ValueError(
                "Either for_seconds or for_blocks must have a value different from None"
            )
