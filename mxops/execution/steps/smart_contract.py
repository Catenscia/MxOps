"""
author: Etienne Wallet

This module contains Steps for smart-contract transactions
"""

from __future__ import annotations
from dataclasses import dataclass, field

from multiversx_sdk import (
    SmartContractController,
    SmartContractTransactionsFactory,
    SmartContractTransactionsOutcomeParser,
    Transaction,
    TransactionOnNetwork,
    TransactionsFactoryConfig,
)
from multiversx_sdk.abi import Abi
from multiversx_sdk.core.errors import BadAddressError
import yaml

from mxops import errors
from mxops.common.providers import MyProxyNetworkProvider
from mxops.config.config import Config
from mxops.data.execution_data import InternalContractData, ScenarioData
from mxops.data.utils import convert_mx_data_to_vanilla, json_dumps
from mxops.execution import utils
from mxops.execution.smart_values import (
    SmartBool,
    SmartInt,
    SmartList,
    SmartPath,
    SmartResultsSaveKeys,
    SmartStr,
    SmartTokenTransfers,
)
from mxops.execution.steps.base import Step, TransactionStep
from mxops.utils.logger import get_logger
from mxops.utils.msc import get_file_hash

LOGGER = get_logger("smart contract steps")


@dataclass
class ContractDeployStep(TransactionStep):
    """
    Represents a smart contract deployment
    """

    wasm_path: SmartPath
    contract_id: SmartStr
    gas_limit: SmartInt
    abi_path: SmartPath | None = None
    upgradeable: SmartBool = field(default_factory=lambda: SmartBool(True))
    readable: SmartBool = field(default_factory=lambda: SmartBool(True))
    payable: SmartBool = field(default_factory=lambda: SmartBool(False))
    payable_by_sc: SmartBool = field(default_factory=lambda: SmartBool(False))
    arguments: SmartList = field(default_factory=lambda: SmartList([]))

    def build_unsigned_transaction(self) -> Transaction:
        """
        Build the transaction for a contract deployment

        :return: transaction built
        :rtype: Transaction
        """
        LOGGER.info(f"Deploying contract {self.contract_id.get_evaluation_string()}")
        scenario_data = ScenarioData.get()

        # check that the id of the contract is free
        contract_id = self.contract_id.get_evaluated_value()
        try:
            scenario_data.get_contract_value(contract_id, "address")
            raise errors.ContractIdAlreadyExists(contract_id)
        except errors.UnknownContract:
            pass

        if self.abi_path is not None:
            abi = Abi.load(self.abi_path.get_evaluated_value())
        else:
            abi = None

        factory_config = TransactionsFactoryConfig(Config.get_config().get("CHAIN"))
        sc_factory = SmartContractTransactionsFactory(factory_config, abi=abi)
        bytecode = self.wasm_path.get_evaluated_value().read_bytes()

        arguments = self.arguments.get_evaluated_value()
        sender = utils.get_address_instance(self.sender.get_evaluated_value())

        return sc_factory.create_transaction_for_deploy(
            sender=sender,
            bytecode=bytecode,
            arguments=arguments,
            gas_limit=self.gas_limit.get_evaluated_value(),
            is_upgradeable=self.upgradeable.get_evaluated_value(),
            is_readable=self.readable.get_evaluated_value(),
            is_payable=self.payable.get_evaluated_value(),
            is_payable_by_sc=self.payable_by_sc.get_evaluated_value(),
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
        contract_id = self.contract_id.get_evaluated_value()
        scenario_data.set_contract_abi_from_source(
            contract_id, self.abi_path.get_evaluated_value()
        )

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
        file_hash = get_file_hash(self.wasm_path.get_evaluated_value())
        contract_data = InternalContractData(
            contract_id=contract_id,
            address=contract_address.to_bech32(),
            saved_values={},
            wasm_hash=file_hash,
            deploy_time=on_chain_tx.timestamp,
            last_upgrade_time=on_chain_tx.timestamp,
        )
        scenario_data.add_contract_data(contract_data)


@dataclass
class ContractUpgradeStep(TransactionStep):
    """
    Represents a smart contract upgrade
    """

    contract: SmartStr
    wasm_path: SmartPath
    gas_limit: SmartInt
    abi_path: SmartPath | None = None
    upgradeable: SmartBool = field(default_factory=lambda: SmartBool(True))
    readable: SmartBool = field(default_factory=lambda: SmartBool(True))
    payable: SmartBool = field(default_factory=lambda: SmartBool(False))
    payable_by_sc: SmartBool = field(default_factory=lambda: SmartBool(False))
    arguments: SmartList = field(default_factory=lambda: SmartList([]))

    def build_unsigned_transaction(self) -> Transaction:
        """
        Build the transaction for a contract upgrade

        :return: transaction built
        :rtype: Transaction
        """
        LOGGER.info(f"Upgrading contract {self.contract.get_evaluation_string()}")

        contract_designation = self.contract.get_evaluated_value()
        contract_address = utils.get_address_instance(contract_designation)

        if self.abi_path is not None:
            abi = Abi.load(self.abi_path.get_evaluated_value())
        else:
            abi = None

        arguments = self.arguments.get_evaluated_value()

        factory_config = TransactionsFactoryConfig(Config.get_config().get("CHAIN"))
        sc_factory = SmartContractTransactionsFactory(factory_config, abi=abi)
        bytecode = self.wasm_path.get_evaluated_value().read_bytes()
        sender = utils.get_address_instance(self.sender.get_evaluated_value())

        return sc_factory.create_transaction_for_upgrade(
            sender=sender,
            contract=contract_address,
            bytecode=bytecode,
            arguments=arguments,
            gas_limit=self.gas_limit.get_evaluated_value(),
            is_upgradeable=self.upgradeable.get_evaluated_value(),
            is_readable=self.readable.get_evaluated_value(),
            is_payable=self.payable.get_evaluated_value(),
            is_payable_by_sc=self.payable_by_sc.get_evaluated_value(),
        )

    def _post_transaction_execution(self, on_chain_tx: TransactionOnNetwork | None):
        """
        Save the new contract data in the Scenario

        :param on_chain_tx: successful upgrade transaction
        :type on_chain_tx: TransactionOnNetwork | None
        """
        if not isinstance(on_chain_tx, TransactionOnNetwork):
            raise ValueError("On chain transaction is None")
        contract = self.contract.get_evaluated_value()
        scenario_data = ScenarioData.get()
        scenario_data.set_contract_abi_from_source(
            contract, self.abi_path.get_evaluated_value()
        )
        try:
            scenario_data.set_contract_value(
                contract, "last_upgrade_time", on_chain_tx.timestamp
            )
        except errors.UnknownContract:  # any contract can be upgraded
            pass


@dataclass
class ContractCallStep(TransactionStep):
    """
    Represents a smart contract endpoint call
    """

    contract: SmartStr
    endpoint: SmartStr
    gas_limit: SmartInt
    arguments: SmartList = field(default_factory=lambda: SmartList([]))
    value: SmartInt = field(default_factory=lambda: SmartInt(0))
    esdt_transfers: SmartTokenTransfers = field(
        default_factory=lambda: SmartTokenTransfers([])
    )
    print_results: SmartBool = field(default_factory=lambda: SmartBool(False))
    results_save_keys: SmartResultsSaveKeys | None = field(default=None)
    returned_data_parts: list | None = field(init=False, default=None)
    saved_results: dict = field(init=False, default_factory=dict)

    def build_unsigned_transaction(self) -> Transaction:
        """
        Build the transaction for a contract call

        :return: transaction built
        :rtype: Transaction
        """
        contract = self.contract.get_evaluated_value()
        endpoint = self.endpoint.get_evaluated_value()
        LOGGER.info(f"Calling {endpoint} for {contract} ")
        scenario_data = ScenarioData.get()

        arguments = self.arguments.get_evaluated_value()
        try:
            contract_abi = scenario_data.get_contract_abi(contract)
        except errors.UnknownAbiContract:
            contract_abi = None

        esdt_transfers = self.esdt_transfers.get_evaluated_value()
        value = self.value.get_evaluated_value()

        factory_config = TransactionsFactoryConfig(Config.get_config().get("CHAIN"))
        sc_factory = SmartContractTransactionsFactory(factory_config, abi=contract_abi)
        sender_address = utils.get_address_instance(self.sender.get_evaluated_value())
        contract_address = utils.get_address_instance(contract)
        gas_limit = self.gas_limit.get_evaluated_value()
        return sc_factory.create_transaction_for_execute(
            sender=sender_address,
            contract=contract_address,
            function=endpoint,
            arguments=arguments,
            gas_limit=gas_limit,
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

        contract = self.contract.get_evaluated_value()
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
        endpoint = self.endpoint.get_evaluated_value()
        outcome = parser.parse_execute(transaction=on_chain_tx, function=endpoint)
        self.returned_data_parts = convert_mx_data_to_vanilla(outcome.values)

        if self.returned_data_parts is None:
            raise ValueError("No data to save")

        if self.results_save_keys is not None:
            results_save_keys = self.results_save_keys.get_evaluated_value()
            to_save = results_save_keys.parse_data_to_save(self.returned_data_parts)
            for save_key, value in to_save.items():
                if save_key is not None:
                    scenario_data.set_contract_value(contract, save_key, value)
                    self.saved_results[save_key] = value

        if self.print_results:
            if self.saved_results is not None:
                print(json_dumps(self.saved_results))
            elif self.returned_data_parts is not None:
                print(json_dumps(self.returned_data_parts))


@dataclass
class ContractQueryStep(Step):
    """
    Represents a smart contract query
    """

    contract: SmartStr
    endpoint: SmartStr
    arguments: SmartList = field(default_factory=lambda: SmartList([]))
    print_results: SmartBool = field(default_factory=lambda: SmartBool(False))
    results_save_keys: SmartResultsSaveKeys | None = field(default=None)
    returned_data_parts: list | None = field(init=False, default=None)
    saved_results: dict = field(init=False, default_factory=dict)

    def save_results(self):
        """
        Save the results the query. This method replace the old way that was using
        expected_results
        """
        scenario_data = ScenarioData.get()
        if self.results_save_keys is None:
            return

        results_save_keys = self.results_save_keys.get_evaluated_value()
        if self.returned_data_parts is None:
            raise ValueError("No data to save")

        LOGGER.info("Saving query results")

        self.saved_results = {}
        contract = self.contract.get_evaluated_value()
        to_save = results_save_keys.parse_data_to_save(self.returned_data_parts)
        for save_key, value in to_save.items():
            if save_key is not None:
                scenario_data.set_contract_value(contract, save_key, value)
                self.saved_results[save_key] = value

    def _execute(self):
        """
        Execute a query and optionally save the result
        """
        endpoint = self.endpoint.get_evaluated_value()
        contract = self.contract.get_evaluated_value()
        LOGGER.info(f"Query on {endpoint} for {contract}")
        scenario_data = ScenarioData.get()
        arguments = self.arguments.get_evaluated_value()
        try:
            contract_abi = scenario_data.get_contract_abi(contract)
        except errors.UnknownAbiContract:
            contract_abi = None

        sc_controller = SmartContractController(
            Config.get_config().get("CHAIN"), MyProxyNetworkProvider(), abi=contract_abi
        )
        contract_address = utils.get_address_instance(contract)
        returned_data_parts = sc_controller.query(
            contract=contract_address,
            function=endpoint,
            arguments=arguments,
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

    sender: SmartStr
    endpoint: SmartStr
    value: SmartInt = field(default_factory=lambda: SmartInt(0))
    esdt_transfers: SmartTokenTransfers = field(
        default_factory=lambda: SmartTokenTransfers([])
    )
    arguments: SmartList = field(default_factory=lambda: SmartList([]))
    expected_outputs: SmartList | None = field(
        default=None
    )  # TODO Replace with checks (success, transfers and results)
    description: SmartStr = field(default_factory=lambda: SmartStr(""))
    gas_limit: SmartInt | None = field(default=None)

    def evaluate_smart_values(self):
        """
        Evaluate all attributes that are smart values
        """
        self.sender.evaluate()
        self.endpoint.evaluate()
        self.value.evaluate()
        self.esdt_transfers.evaluate()
        self.arguments.evaluate()
        if self.expected_outputs is not None:
            self.expected_outputs.evaluate()
        self.description.evaluate()
        if self.gas_limit is not None:
            self.gas_limit.evaluate()

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
        data_copy["sender"] = SmartStr(data_copy["sender"])
        data_copy["endpoint"] = SmartStr(data_copy["endpoint"])
        if "value" in data_copy:
            data_copy["value"] = SmartInt(data_copy["value"])
        if "esdt_transfers" in data_copy:
            data_copy["esdt_transfers"] = SmartTokenTransfers(
                data_copy["esdt_transfers"]
            )
        if "arguments" in data_copy:
            data_copy["arguments"] = SmartList(data_copy["arguments"])
        if (
            "expected_outputs" in data_copy
            and data_copy["expected_outputs"] is not None
        ):
            data_copy["expected_outputs"] = SmartList(data_copy["expected_outputs"])
        if "description" in data_copy:
            data_copy["description"] = SmartStr(data_copy["description"])
        if "gas_limit" in data_copy and data_copy["gas_limit"] is not None:
            data_copy["gas_limit"] = SmartInt(data_copy["gas_limit"])

        return FuzzExecutionParameters(**data_copy)


@dataclass
class FileFuzzerStep(Step):
    """
    Represents fuzzing tests where the inputs and expected outputs from each test
    are taken from a file
    """

    contract: SmartStr
    file_path: SmartPath

    def load_executions_parameters(self) -> list[FuzzExecutionParameters]:
        """
        Load the executions parameters for the fuzz tests as described by the file

        :return: executions parameters
        :rtype: list[FuzzExecutionParameters]
        """
        file_extension = self.file_path.get_evaluated_value().suffix
        if file_extension in (".yaml", ".yml"):
            return self.load_executions_parameters_from_yaml()
        raise errors.WrongFuzzTestFile(
            f"Extension {file_extension} is not supported for file "
            f"{self.file_path.get_evaluation_string()}"
        )

    def load_executions_parameters_from_yaml(self) -> list[FuzzExecutionParameters]:
        """
        Load the executions parameters for the fuzz tests as described by the file,
        which is assumed to be a yaml file

        :return: executions parameters
        :rtype: list[FuzzExecutionParameters]
        """
        parameters = []
        with open(
            self.file_path.get_evaluated_value().as_posix(), "r", encoding="utf-8"
        ) as file:
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

    def _execute(self):
        """
        Execute fuzz testing on the given contract using the parameters
        from the provided file
        """
        contract = self.contract.get_evaluated_value()
        scenario_data = ScenarioData.get()
        try:
            contract_abi = scenario_data.get_contract_raw_abi(contract)
        except errors.UnknownAbiContract as err:
            raise errors.WrongFuzzTestFile(
                "ABI file must be provided for fuzz testing"
            ) from err
        LOGGER.info(
            f"Executing fuzz testing from file {self.file_path.get_evaluation_string()}"
        )
        exec_parameters = self.load_executions_parameters()
        n_tests = len(exec_parameters)
        LOGGER.info(f"Found {n_tests} tests")
        for i, params in enumerate(exec_parameters):
            params.evaluate_smart_values()
            LOGGER.info(
                f"Executing fuzz test n°{i + 1}/{n_tests} ({i / n_tests:.0%}): "
                f"{params.description.get_evaluated_value()}"
            )
            self._execute_fuzz(contract_abi, params)
        LOGGER.info("Fuzzing execution complete (100%)")

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
            if e["name"] == execution_parameters.endpoint.get_evaluated_value():
                endpoint = e
                break
        if endpoint is None:
            raise errors.WrongFuzzTestFile(
                f"Endpoint {execution_parameters.endpoint.get_evaluation_string()} "
                f"not found in the contract abi {contract_abi['name']}"
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
        contract = self.contract.get_evaluated_value()
        save_key = "fuzz_test_query_results"
        query_step = ContractQueryStep(
            contract,
            execution_parameters.endpoint.get_evaluated_value(),
            arguments=execution_parameters.arguments.get_evaluated_value(),
            results_save_keys=save_key,
        )
        query_step.execute()
        if execution_parameters.expected_outputs is None:
            return

        scenario_data = ScenarioData.get()
        results = scenario_data.get_contract_value(contract, save_key)
        if results != execution_parameters.expected_outputs.get_evaluated_value():
            raise errors.FuzzTestFailed(
                f"Outputs are different from expected: found {results} but wanted "
                f"{execution_parameters.expected_outputs.get_evaluation_string()}"
            )

    def _execute_fuzz_call(self, execution_parameters: FuzzExecutionParameters):
        """
        Execute one instance of fuzz test that is considered as a query execution

        :param execution_parameters: parameters of the test to execute
        :type execution_parameters: FuzzExecutionParameters
        """
        contract = self.contract.get_evaluated_value()
        save_key = "fuzz_test_call_results"
        call_step = ContractCallStep(
            contract=contract,
            endpoint=execution_parameters.endpoint.get_evaluated_value(),
            gas_limit=execution_parameters.gas_limit.get_evaluated_value(),
            arguments=execution_parameters.arguments.get_evaluated_value(),
            value=execution_parameters.value.get_evaluated_value(),
            esdt_transfers=execution_parameters.esdt_transfers.get_evaluated_value(),
            sender=execution_parameters.sender.get_evaluated_value(),
            results_save_keys=save_key,
        )
        call_step.execute()
        if execution_parameters.expected_outputs is None:
            return

        scenario_data = ScenarioData.get()
        results = scenario_data.get_contract_value(contract, save_key)
        if results != execution_parameters.expected_outputs.get_evaluated_value():
            raise errors.FuzzTestFailed(
                f"Outputs are different from expected: found {results} but wanted "
                f"{execution_parameters.expected_outputs.get_evaluation_string()}"
            )
