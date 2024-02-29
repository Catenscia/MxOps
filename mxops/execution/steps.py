"""
author: Etienne Wallet

This module contains the classes used to execute scenes in a scenario
"""

from __future__ import annotations
import base64
from dataclasses import dataclass, field
from importlib.util import spec_from_file_location, module_from_spec
import os
from pathlib import Path
import sys
import time
from typing import Any, ClassVar, Dict, Iterator, List, Optional, Set, Union

from multiversx_sdk_cli.contracts import QueryResult
from multiversx_sdk_cli.constants import DEFAULT_HRP
from multiversx_sdk_core import (
    Address,
    TokenComputer,
    Token,
    TokenTransfer,
    ContractQueryBuilder,
    Transaction,
)
from multiversx_sdk_core.serializer import arg_to_string
from multiversx_sdk_core.transaction_factories import (
    TransactionsFactoryConfig,
    SmartContractTransactionsFactory,
    TransferTransactionsFactory,
)
from multiversx_sdk_network_providers import ProxyNetworkProvider
from multiversx_sdk_network_providers.transactions import TransactionOnNetwork
from multiversx_sdk_network_providers.contract_query_response import (
    ContractQueryResponse,
)
from mxpyserializer.abi_serializer import AbiSerializer

from mxops.config.config import Config
from mxops.data.execution_data import InternalContractData, ScenarioData, TokenData
from mxops.data.utils import json_dumps
from mxops.enums import TokenTypeEnum
from mxops.execution import utils
from mxops.execution.token_management_factory import (
    MyTokenManagementTransactionsFactory,
)
from mxops.execution.account import AccountsManager
from mxops.execution import token_management as tkm
from mxops.execution.checks import Check, SuccessCheck, instanciate_checks
from mxops.execution.msc import EsdtTransfer
from mxops.execution.network import send, send_and_wait_for_result
from mxops.execution.utils import parse_query_result
from mxops.utils.logger import get_logger
from mxops.utils.msc import get_file_hash, get_tx_link
from mxops import errors

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
    def from_dict(cls, data: Dict) -> Step:
        """
        Instantiate a Step instance from a dictionary

        :return: step instance
        :rtype: Step
        """
        return cls(**data)


@dataclass(kw_only=True)
class TransactionStep(Step):
    """
    Represents a step that produce and send a transaction
    """

    sender: str
    checks: List[Check] = field(default_factory=lambda: [SuccessCheck()])

    def __post_init__(self):
        """
        After the initialisation of an instance, if the checks are
        found to be Dict, will try to convert them to Checks instances.
        Usefull for easy loading from yaml files
        """
        if len(self.checks) > 0 and isinstance(self.checks[0], Dict):
            self.checks = instanciate_checks(self.checks)

    def _build_unsigned_transaction(self) -> Transaction:
        """
        Interface for the method that will build transaction to send. This transaction
        is meant to contain all the data specific to this Step.
        The signature will be done at a later stage in the method sign_transaction

        :return: transaction created by the Step
        :rtype: Transaction
        """
        raise NotImplementedError

    def sign_transaction(self, tx: Transaction):
        """
        Sign the transaction created by this step and update the account nonce

        :param tx: tra
        :type tx: Transaction
        """
        sender_account = AccountsManager.get_account(self.sender)
        tx.nonce = sender_account.nonce
        tx.signature = bytes.fromhex(sender_account.sign_transaction(tx))
        sender_account.nonce += 1

    def _post_transaction_execution(self, on_chain_tx: TransactionOnNetwork | None):
        """
        Interface for the function that will be executed after the transaction has
        been successfully executed

        :param on_chain_tx: on chain transaction that was sent by the Step
        :type on_chain_tx: TransactionOnNetwork | None
        """

    def execute(self):
        """
        Execute the workflow for a transaction Step: build, send, check
        and post execute
        """
        tx = self._build_unsigned_transaction()
        self.sign_transaction(tx)

        if len(self.checks) > 0:
            on_chain_tx = send_and_wait_for_result(tx)
            for check in self.checks:
                check.raise_on_failure(on_chain_tx)
            LOGGER.info(f"Transaction successful: {get_tx_link(on_chain_tx.hash)}")
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

    steps: List[Step]
    var_name: str
    var_start: int = None
    var_end: int = None
    var_list: List[int] = None

    def generate_steps(self) -> Iterator[Step]:
        """
        Generate the steps that sould be executed

        :yield: steps to be executed
        :rtype: Iterator[Step]
        """
        if self.var_start is not None and self.var_end is not None:
            iterator = range(self.var_start, self.var_end)
        elif self.var_list is not None:
            iterator = self.var_list
        else:
            raise ValueError("Loop iteration is not correctly defined")
        for var in iterator:
            os.environ[self.var_name] = str(var)
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
        found to be Dict, will try to convert them to Steps instances.
        Usefull for easy loading from yaml files
        """
        if len(self.steps) > 0 and isinstance(self.steps[0], Dict):
            self.steps = instanciate_steps(self.steps)


@dataclass
class ContractDeployStep(TransactionStep):
    """
    Represents a smart contract deployment
    """

    wasm_path: str
    contract_id: str
    gas_limit: int
    abi_path: Optional[str] = None
    upgradeable: bool = True
    readable: bool = True
    payable: bool = False
    payable_by_sc: bool = False
    arguments: List = field(default_factory=list)

    def _build_unsigned_transaction(self) -> Transaction:
        """
        Build the transaction for a contract deployment

        :return: transaction built
        :rtype: Transaction
        """
        LOGGER.info(f"Deploying contract {self.contract_id}")
        scenario_data = ScenarioData.get()

        # check that the id of the contract is free
        try:
            scenario_data.get_contract_value(self.contract_id, "address")
            raise errors.ContractIdAlreadyExists(self.contract_id)
        except errors.UnknownContract:
            pass

        if self.abi_path is not None:
            serializer = AbiSerializer.from_abi(Path(self.abi_path))
        else:
            serializer = None

        retrieved_arguments = utils.retrieve_value_from_any(self.arguments)
        if serializer is None:
            deploy_args = utils.format_tx_arguments(retrieved_arguments)
        else:
            deploy_args = serializer.encode_endpoint_inputs("init", retrieved_arguments)

        factory_config = TransactionsFactoryConfig(Config.get_config().get("CHAIN"))
        sc_factory = SmartContractTransactionsFactory(factory_config, TokenComputer())
        bytecode = Path(self.wasm_path).read_bytes()

        return sc_factory.create_transaction_for_deploy(
            sender=utils.get_address_instance(self.sender),
            bytecode=bytecode,
            arguments=deploy_args,
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
        contract_address = None
        for event in on_chain_tx.logs.events:
            if event.identifier == "SCDeploy":
                hex_address = event.topics[0].hex()
                contract_address = Address.from_hex(hex_address, hrp=DEFAULT_HRP)

        if not isinstance(contract_address, Address):
            raise errors.ParsingError(on_chain_tx, "contract deployment address")

        if self.abi_path is not None:
            serializer = AbiSerializer.from_abi(Path(self.abi_path))
        else:
            serializer = None

        contract_data = InternalContractData(
            contract_id=self.contract_id,
            address=contract_address.bech32(),
            saved_values={},
            wasm_hash=get_file_hash(Path(self.wasm_path)),
            deploy_time=on_chain_tx.timestamp,
            last_upgrade_time=on_chain_tx.timestamp,
            serializer=serializer,
        )
        scenario_data.add_contract_data(contract_data)


@dataclass
class ContractUpgradeStep(TransactionStep):
    """
    Represents a smart contract upgrade
    """

    sender: Dict
    contract: str
    wasm_path: str
    gas_limit: int
    upgradeable: bool = True
    readable: bool = True
    payable: bool = False
    payable_by_sc: bool = False
    arguments: List = field(default_factory=lambda: [])
    abi_path: Optional[str] = None

    def _build_unsigned_transaction(self) -> Transaction:
        """
        Build the transaction for a contract upgrade

        :return: transaction built
        :rtype: Transaction
        """
        LOGGER.info(f"Upgrading contract {self.contract}")

        if self.abi_path is not None:
            serializer = AbiSerializer.from_abi(Path(self.abi_path))
        else:
            serializer = None

        retrieved_arguments = utils.retrieve_value_from_any(self.arguments)
        if serializer is None:
            upgrade_args = utils.format_tx_arguments(retrieved_arguments)
        else:
            upgrade_args = serializer.encode_endpoint_inputs(
                "upgrade", retrieved_arguments
            )

        factory_config = TransactionsFactoryConfig(Config.get_config().get("CHAIN"))
        sc_factory = SmartContractTransactionsFactory(factory_config, TokenComputer())
        bytecode = Path(self.wasm_path).read_bytes()

        return sc_factory.create_transaction_for_upgrade(
            sender=utils.get_address_instance(self.sender),
            contract=utils.get_address_instance(self.contract),
            bytecode=bytecode,
            arguments=upgrade_args,
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

        if self.abi_path is not None:
            serializer = AbiSerializer.from_abi(Path(self.abi_path))
        else:
            serializer = None

        scenario_data = ScenarioData.get()
        try:
            scenario_data.set_contract_value(
                self.contract, "last_upgrade_time", on_chain_tx.timestamp
            )
            if serializer is not None:
                scenario_data.set_contract_value(
                    self.contract, "serializer", serializer
                )
        except errors.UnknownContract:  # any contract can be upgraded
            pass


@dataclass
class ContractCallStep(TransactionStep):
    """
    Represents a smart contract endpoint call
    """

    contract: str
    endpoint: str
    gas_limit: int
    arguments: List = field(default_factory=lambda: [])
    value: int | str = 0
    esdt_transfers: List[EsdtTransfer] = field(default_factory=lambda: [])

    def _build_unsigned_transaction(self) -> Transaction:
        """
        Build the transaction for a contract call

        :return: transaction built
        :rtype: Transaction
        """
        LOGGER.info(f"Calling {self.endpoint} for {self.contract}")
        scenario_data = ScenarioData.get()

        retrieved_arguments = utils.retrieve_value_from_any(self.arguments)
        try:
            serializer = scenario_data.get_contract_value(self.contract, "serializer")
        except errors.UnknownContract:
            serializer = None

        if isinstance(serializer, AbiSerializer):
            call_args = serializer.encode_endpoint_inputs(
                self.endpoint, retrieved_arguments
            )
        else:
            call_args = utils.format_tx_arguments(retrieved_arguments)

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
        sc_factory = SmartContractTransactionsFactory(factory_config, TokenComputer())

        return sc_factory.create_transaction_for_execute(
            sender=utils.get_address_instance(self.sender),
            contract=utils.get_address_instance(self.contract),
            function=self.endpoint,
            arguments=call_args,
            gas_limit=self.gas_limit,
            native_transfer_amount=value,
            token_transfers=esdt_transfers,
        )

    def __post_init__(self):
        """
        After the initialisation of an instance, if the esdt transfers are
        found to be Dict,
        will try to convert them to EsdtTransfers instances.
        Usefull for easy loading from yaml files
        """
        super().__post_init__()
        checked_transfers = []
        for trf in self.esdt_transfers:
            if isinstance(trf, EsdtTransfer):
                checked_transfers.append(trf)
            elif isinstance(trf, Dict):
                checked_transfers.append(EsdtTransfer(**trf))
            else:
                raise ValueError(f"Unexpected type: {type(trf)}")
        self.esdt_transfers = checked_transfers


@dataclass
class ResultsSaveKeys:
    master_key: Optional[str]
    sub_keys: Optional[List[Optional[str]]]

    @staticmethod
    def from_input(data: Any) -> Optional[ResultsSaveKeys]:
        """
        Parse the user input as an instance of this class

        :param data: input data for a yaml Scene file
        :type data: Any
        :return: results save keys if defined
        :rtype: Optional[ResultsSaveKeys]
        """
        if data is None:
            return None
        if isinstance(data, str):
            return ResultsSaveKeys(data, None)
        if isinstance(data, List):
            for save_key in data:
                if not isinstance(save_key, str) and save_key is not None:
                    raise TypeError(f"Save keys must be a str or None, got {save_key}")
            return ResultsSaveKeys(None, data)
        if isinstance(data, Dict):
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


@dataclass
class ContractQueryStep(Step):
    """
    Represents a smart contract query
    """

    contract: str
    endpoint: str
    arguments: List = field(default_factory=lambda: [])
    expected_results: List[Dict[str, str]] = field(default_factory=lambda: [])
    print_results: bool = False
    results: List[QueryResult] | None = field(init=False, default=None)
    query_response: ContractQueryResponse | None = field(init=False, default=None)
    decoded_results: List[Any] | None = field(init=False, default=None)
    saved_results: List[Any] | None = field(init=False, default=None)
    results_save_keys: Optional[ResultsSaveKeys] = field(default=None)
    results_types: Union[None, List[Dict]] = field(default=None)

    def __post_init__(self):
        """
        After the initialisation of an instance, if the esdt transfers are
        found to be Dict,
        will try to convert them to EsdtTransfers instances.
        Usefull for easy loading from yaml files
        """
        if self.results_save_keys is not None and not isinstance(
            self.results_save_keys, ResultsSaveKeys
        ):
            self.results_save_keys = ResultsSaveKeys.from_input(self.results_save_keys)
        if self.results_types is not None:
            if not isinstance(self.results_types, list):
                raise errors.InvalidQueryResultsDefinition
            for result_type in self.results_types:
                if not isinstance(result_type, dict):
                    raise errors.InvalidQueryResultsDefinition
                if "type" not in result_type:
                    raise errors.InvalidQueryResultsDefinition

    def _interpret_return_data(self, data: str) -> QueryResult:
        """
        Function to interpret the returned data from a query when there is no Serializer
        available

        :param data: data from the query response
        :type data: str
        :return: Result of the query
        :rtype: QueryResult
        """
        if not data:
            return QueryResult("", "", None)

        try:
            as_bytes = base64.b64decode(data)
            as_hex = as_bytes.hex()
            try:
                as_int = int(str(int(as_hex or "0", 16)))
            except (ValueError, TypeError):
                as_int = None
            result = QueryResult(data, as_hex, as_int)
            return result
        except Exception as err:
            raise errors.ParsingError(data, "QueryResult") from err

    def save_results(self):
        """
        Save the results the query. This method replace the old way that was using
        expected_results
        """
        scenario_data = ScenarioData.get()
        if self.results_save_keys is None:
            return

        if self.decoded_results is None:
            raise ValueError("No decoded results to save")

        LOGGER.info("Saving query results")
        sub_keys = self.results_save_keys.sub_keys
        if sub_keys is not None:
            if len(sub_keys) != len(self.decoded_results):
                raise ValueError(
                    f"Number of results ({len(self.decoded_results)} -> "
                    f"{self.decoded_results}) and save keys "
                    f"({len(sub_keys)} -> {sub_keys}) doesn't match"
                )
            to_save = dict(zip(sub_keys, self.decoded_results))
            if self.results_save_keys.master_key is not None:
                to_save = {self.results_save_keys.master_key: to_save}
        else:
            to_save = {self.results_save_keys.master_key: self.decoded_results}

        self.saved_results = {}
        for save_key, value in to_save.items():
            if save_key is not None:
                scenario_data.set_contract_value(self.contract, save_key, value)
                self.saved_results[save_key] = value

    def execute(self):
        """
        Execute a query and optionally save the result
        """
        LOGGER.info(f"Query on {self.endpoint} for {self.contract}")
        config = Config.get_config()
        scenario_data = ScenarioData.get()
        retrieved_arguments = utils.retrieve_value_from_any(self.arguments)
        try:
            serializer = scenario_data.get_contract_value(self.contract, "serializer")
        except errors.UnknownContract:
            serializer = None

        if isinstance(serializer, AbiSerializer):
            query_args = serializer.encode_endpoint_inputs(
                self.endpoint, retrieved_arguments
            )
        else:
            query_args = utils.format_tx_arguments(retrieved_arguments)

        builder = ContractQueryBuilder(
            contract=utils.get_address_instance(self.contract),
            function=self.endpoint,
            call_arguments=query_args,
        )
        query = builder.build()
        proxy = ProxyNetworkProvider(config.get("PROXY"))

        query_failed = True
        n_attempts = 0
        max_attempts = int(Config.get_config().get("MAX_QUERY_ATTEMPTS"))
        while query_failed and n_attempts < max_attempts:
            n_attempts += 1
            self.query_response = proxy.query_contract(query)
            query_failed = self.query_response.return_code != "ok"
            if query_failed:
                time.sleep(3)
                LOGGER.warning(
                    f"Query failed: {self.query_response.return_message}. Attempt "
                    f"{n_attempts}/{max_attempts}"
                )
            else:
                self.results = [
                    self._interpret_return_data(data)
                    for data in self.query_response.return_data
                ]
                if self.results_types is not None:
                    data_parts = self.query_response.get_return_data_parts()
                    self.decoded_results = AbiSerializer().decode_io(
                        self.results_types, data_parts
                    )
                elif serializer is not None:
                    self.decoded_results = serializer.decode_contract_query_response(
                        self.endpoint, self.query_response
                    )

        if query_failed:
            self.results = None
            raise errors.QueryFailed

        if len(self.expected_results) > 0:
            LOGGER.warning(
                "expected_results is deprecated, please use results_save_key and "
                "results_types instead. https://mxops.readthedocs.io/en/stable/user_doc"
                "umentation/steps.html#contract-query-step"
            )
            LOGGER.info("Saving Query results as contract data")
            for result, expected_result in zip(self.results, self.expected_results):
                parsed_result = parse_query_result(
                    result, expected_result["result_type"]
                )
                scenario_data.set_contract_value(
                    self.contract, expected_result["save_key"], parsed_result
                )
        else:
            self.save_results()

        if self.print_results:
            if self.saved_results is not None:
                print(json_dumps(self.saved_results))
            elif self.decoded_results is not None:
                print(json_dumps(self.decoded_results))
            else:
                print(self.results)

        LOGGER.info("Query successful")


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
    can_mint: bool = False
    can_burn: bool = False
    can_change_owner: bool = False
    can_upgrade: bool = False
    can_add_special_roles: bool = False

    def _build_unsigned_transaction(self) -> Transaction:
        """
        Build the transaction to issue a fungible token

        :return: transaction built
        :rtype: Transaction
        """
        sender = utils.get_address_instance(self.sender)
        LOGGER.info(
            f"Issuing fungible token named {self.token_name} "
            f"for the account {self.sender} ({sender.bech32()})"
        )
        factory_config = TransactionsFactoryConfig(Config.get_config().get("CHAIN"))
        tx_factory = MyTokenManagementTransactionsFactory(factory_config)
        if self.can_mint or self.can_burn:
            LOGGER.warning(
                "the roles CanMint and CanBurn are deprecated on the blockchain, they "
                "are now useless"
            )

        return tx_factory.create_transaction_for_issuing_fungible(
            sender=sender,
            token_name=self.token_name,
            token_ticker=self.token_ticker,
            initial_supply=self.initial_supply,
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
        scenario_data = ScenarioData.get()
        token_identifier = tkm.extract_new_token_identifier(on_chain_tx)
        LOGGER.info(f"Newly issued token got the identifier {token_identifier}")
        scenario_data.add_token_data(
            TokenData(
                name=self.token_name,
                ticker=self.token_ticker,
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

    def _build_unsigned_transaction(self) -> Transaction:
        """
        Build the transaction to issue a non fungible token

        :return: transaction built
        :rtype: Transaction
        """
        sender = utils.get_address_instance(self.sender)
        LOGGER.info(
            f"Issuing non fungible token named {self.token_name} "
            f"for the account {self.sender} ({sender.bech32()})"
        )
        factory_config = TransactionsFactoryConfig(Config.get_config().get("CHAIN"))
        tx_factory = MyTokenManagementTransactionsFactory(factory_config)
        return tx_factory.create_transaction_for_issuing_non_fungible(
            sender=sender,
            token_name=self.token_name,
            token_ticker=self.token_ticker,
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
        scenario_data = ScenarioData.get()
        token_identifier = tkm.extract_new_token_identifier(on_chain_tx)
        LOGGER.info(f"Newly issued token got the identifier {token_identifier}")
        scenario_data.add_token_data(
            TokenData(
                name=self.token_name,
                ticker=self.token_ticker,
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

    def _build_unsigned_transaction(self) -> Transaction:
        """
        Build the transaction to issue a semi fungible token

        :return: transaction built
        :rtype: Transaction
        """
        sender = utils.get_address_instance(self.sender)
        LOGGER.info(
            f"Issuing semi fungible token named {self.token_name} "
            f"for the account {self.sender} ({sender.bech32()})"
        )
        factory_config = TransactionsFactoryConfig(Config.get_config().get("CHAIN"))
        tx_factory = MyTokenManagementTransactionsFactory(factory_config)
        return tx_factory.create_transaction_for_issuing_semi_fungible(
            sender=sender,
            token_name=self.token_name,
            token_ticker=self.token_ticker,
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
        scenario_data = ScenarioData.get()
        token_identifier = tkm.extract_new_token_identifier(on_chain_tx)
        LOGGER.info(f"Newly issued token got the identifier {token_identifier}")
        scenario_data.add_token_data(
            TokenData(
                name=self.token_name,
                ticker=self.token_ticker,
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

    def _build_unsigned_transaction(self) -> Transaction:
        """
        Build the transaction to issue a meta token

        :return: transaction built
        :rtype: Transaction
        """
        sender = utils.get_address_instance(self.sender)
        LOGGER.info(
            f"Issuing meta token named {self.token_name} "
            f"for the account {self.sender} ({sender.bech32()})"
        )
        factory_config = TransactionsFactoryConfig(Config.get_config().get("CHAIN"))
        tx_factory = MyTokenManagementTransactionsFactory(factory_config)
        return tx_factory.create_transaction_for_registering_meta_esdt(
            sender=sender,
            token_name=self.token_name,
            token_ticker=self.token_ticker,
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
        scenario_data = ScenarioData.get()
        token_identifier = tkm.extract_new_token_identifier(on_chain_tx)
        LOGGER.info(f"Newly issued token got the identifier {token_identifier}")
        scenario_data.add_token_data(
            TokenData(
                name=self.token_name,
                ticker=self.token_ticker,
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
    roles: List[str]
    ALLOWED_ROLES: ClassVar[Set] = set()

    def __post_init__(self):
        super().__post_init__()
        for role in self.roles:
            if role not in self.ALLOWED_ROLES:
                raise ValueError(
                    f"role {role} is not in allowed roles {self.ALLOWED_ROLES}"
                )


@dataclass
class ManageFungibleTokenRolesStep(ManageTokenRolesStep):
    """
    This step is used to set or unset roles for an adress on a fungible token
    """

    ALLOWED_ROLES: ClassVar[Set] = {
        "ESDTRoleLocalBurn",
        "ESDTRoleLocalMint",
        "ESDTTransferRole",
    }

    def _build_unsigned_transaction(self) -> Transaction:
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
        tx_factory = MyTokenManagementTransactionsFactory(factory_config)

        if self.is_set:
            return tx_factory.create_transaction_for_setting_special_role_on_fungible_token(  # noqa: E501
                sender=sender,
                user=target,
                token_identifier=token_identifier,
                add_role_local_mint="ESDTRoleLocalBurn" in self.roles,
                add_role_local_burn="ESDTRoleLocalMint" in self.roles,
                add_transfer_role="ESDTTransferRole" in self.roles,
            )
        return tx_factory.create_transaction_for_unsetting_special_role_on_fungible_token(  # noqa: E501
            sender=sender,
            user=target,
            token_identifier=token_identifier,
            remove_role_local_mint="ESDTRoleLocalBurn" in self.roles,
            remove_role_local_burn="ESDTRoleLocalMint" in self.roles,
            remove_transfer_role="ESDTTransferRole" in self.roles,
        )


@dataclass
class ManageNonFungibleTokenRolesStep(ManageTokenRolesStep):
    """
    This step is used to set or unset roles for an adress on a non fungible token
    """

    ALLOWED_ROLES: ClassVar[Set] = {
        "ESDTRoleNFTCreate",
        "ESDTRoleNFTBurn",
        "ESDTRoleNFTUpdateAttributes",
        "ESDTRoleNFTAddURI",
        "ESDTTransferRole",
    }

    def _build_unsigned_transaction(self) -> Transaction:
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
        tx_factory = MyTokenManagementTransactionsFactory(factory_config)

        if self.is_set:
            return tx_factory.create_transaction_for_setting_special_role_on_non_fungible_token(  # noqa: E501
                sender=sender,
                user=target,
                token_identifier=token_identifier,
                add_role_nft_create="ESDTRoleNFTCreate" in self.roles,
                add_role_nft_burn="ESDTRoleNFTBurn" in self.roles,
                add_role_nft_update_attributes="ESDTRoleNFTUpdateAttributes"
                in self.roles,
                add_role_nft_add_uri="ESDTRoleNFTAddURI" in self.roles,
                add_role_esdt_transfer_role="ESDTTransferRole" in self.roles,
            )
        return tx_factory.create_transaction_for_unsetting_special_role_on_non_fungible_token(  # noqa: E501
            sender=sender,
            user=target,
            token_identifier=token_identifier,
            remove_role_nft_create="ESDTRoleNFTCreate" in self.roles,
            remove_role_nft_burn="ESDTRoleNFTBurn" in self.roles,
            remove_role_nft_update_attributes="ESDTRoleNFTUpdateAttributes"
            in self.roles,
            remove_role_nft_add_uri="ESDTRoleNFTAddURI" in self.roles,
            remove_role_esdt_transfer_role="ESDTTransferRole" in self.roles,
        )


@dataclass
class ManageSemiFungibleTokenRolesStep(ManageTokenRolesStep):
    """
    This step is used to set or unset roles for an adress on a semi fungible token
    """

    ALLOWED_ROLES: ClassVar[Set] = {
        "ESDTRoleNFTCreate",
        "ESDTRoleNFTBurn",
        "ESDTRoleNFTAddQuantity",
        "ESDTTransferRole",
    }

    def _build_unsigned_transaction(self) -> Transaction:
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
        tx_factory = MyTokenManagementTransactionsFactory(factory_config)

        if self.is_set:
            return tx_factory.create_transaction_for_setting_special_role_on_semi_fungible_token(  # noqa: E501
                sender=sender,
                user=target,
                token_identifier=token_identifier,
                add_role_nft_create="ESDTRoleNFTCreate" in self.roles,
                add_role_nft_burn="ESDTRoleNFTBurn" in self.roles,
                add_role_nft_add_quantity="ESDTRoleNFTAddQuantity" in self.roles,
                add_role_esdt_transfer_role="ESDTTransferRole" in self.roles,
            )
        return tx_factory.create_transaction_for_unsetting_special_role_on_semi_fungible_token(  # noqa: E501
            sender=sender,
            user=target,
            token_identifier=token_identifier,
            remove_role_nft_create="ESDTRoleNFTCreate" in self.roles,
            remove_role_nft_burn="ESDTRoleNFTBurn" in self.roles,
            remove_role_nft_add_quantity="ESDTRoleNFTAddQuantity" in self.roles,
            remove_role_esdt_transfer_role="ESDTTransferRole" in self.roles,
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
    amount: Union[str, int]

    def _build_unsigned_transaction(self) -> Transaction:
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
        tx_factory = MyTokenManagementTransactionsFactory(factory_config)
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
    amount: Union[str, int]
    name: str = ""
    royalties: Union[str, int] = 0
    hash: str = ""
    attributes: str = ""
    uris: List[str] = field(default_factory=lambda: [])

    def _build_unsigned_transaction(self) -> Transaction:
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
        tx_factory = MyTokenManagementTransactionsFactory(factory_config)
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
        new_nonce = tkm.extract_new_nonce(on_chain_tx)
        LOGGER.info(f"Newly issued nonce is {new_nonce}")


@dataclass
class EgldTransferStep(TransactionStep):
    """
    This step is used to transfer some eGLD to an address
    """

    receiver: str
    amount: Union[str, int]

    def _build_unsigned_transaction(self) -> Transaction:
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
        tr_factory = TransferTransactionsFactory(factory_config, TokenComputer())
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
    amount: Union[str, int]

    def _build_unsigned_transaction(self) -> Transaction:
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
        tr_factory = TransferTransactionsFactory(factory_config, TokenComputer())
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
    nonce: Union[str, int]
    amount: Union[str, int]

    def _build_unsigned_transaction(self) -> Transaction:
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

        esdt_transfers = [TokenTransfer(Token(token_identifier, nonce), amount)]

        LOGGER.info(
            f"Sending {amount} {token_identifier}-{arg_to_string(nonce)} from "
            f"{self.sender} ({sender.bech32()}) to {self.receiver} "
            f"({receiver.bech32()})"
        )
        factory_config = TransactionsFactoryConfig(Config.get_config().get("CHAIN"))
        tr_factory = TransferTransactionsFactory(factory_config, TokenComputer())
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
    transfers: List[EsdtTransfer]

    def __post_init__(self):
        """
        After the initialisation of an instance, if the esdt transfers are
        found to be Dict,
        will try to convert them to EsdtTransfers instances.
        Usefull for easy loading from yaml files
        """
        super().__post_init__()
        checked_transfers = []
        for trf in self.transfers:
            if isinstance(trf, EsdtTransfer):
                checked_transfers.append(trf)
            elif isinstance(trf, Dict):
                checked_transfers.append(EsdtTransfer(**trf))
            else:
                raise ValueError(f"Unexpected type: {type(trf)}")
        self.transfers = checked_transfers

    def _build_unsigned_transaction(self) -> Transaction:
        """
        Build the transaction for multiple transfers

        :return: transaction built
        :rtype: Transaction
        """
        sender = utils.get_address_instance(self.sender)
        receiver = utils.get_address_instance(self.receiver)
        esdt_transfers = []
        esdt_transfers_strs = []
        for trf in self.transfers:
            token_identifier = utils.retrieve_value_from_string(trf.token_identifier)
            amount = int(utils.retrieve_value_from_any(trf.amount))
            nonce = int(utils.retrieve_value_from_any(trf.nonce))

            esdt_transfers.append(TokenTransfer(Token(token_identifier, nonce), amount))
            esdt_transfers_strs.append(
                f"{amount} {token_identifier}-{arg_to_string(nonce)}"
            )

        LOGGER.info(
            f"Sending {', '.join(esdt_transfers_strs)} from {self.sender} "
            f"({sender.bech32()}) to {self.receiver} ({receiver.bech32()})"
        )
        factory_config = TransactionsFactoryConfig(Config.get_config().get("CHAIN"))
        tr_factory = TransferTransactionsFactory(factory_config, TokenComputer())
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
        user_function = getattr(user_module, self.function)

        # transform args and kwargs and execute
        retrieved_arguments = utils.retrieve_value_from_any(self.arguments)
        retrieved_keyword_arguments = utils.retrieve_value_from_any(
            self.keyword_arguments
        )
        result = user_function(*retrieved_arguments, **retrieved_keyword_arguments)

        if result:
            if isinstance(result, str):
                var_name = f"MXOPS_{self.function.upper()}_RESULT"
                os.environ[var_name] = result
            else:
                LOGGER.warning(
                    f"The result of the function {self.function} is not a "
                    "string and has not been saved"
                )

        LOGGER.info(f"Function result: {result}")


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


def instanciate_steps(raw_steps: List[Dict]) -> List[Step]:
    """
    Take steps as dictionaries and convert them to their corresponding step classes.

    :param raw_steps: steps to instantiate
    :type raw_steps: List[Dict]
    :return: steps instances
    :rtype: List[Step]
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
