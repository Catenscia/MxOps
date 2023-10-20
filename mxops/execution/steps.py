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
from typing import ClassVar, Dict, Iterator, List, Set, Union

from multiversx_sdk_cli.contracts import QueryResult
from multiversx_sdk_cli.constants import DEFAULT_HRP
from multiversx_sdk_core import (
    Address,
    TokenPayment,
    ContractQueryBuilder,
    CodeMetadata,
)
from multiversx_sdk_core import transaction_builders as tx_builder
from multiversx_sdk_core.serializer import arg_to_string
from multiversx_sdk_network_providers import ProxyNetworkProvider
from multiversx_sdk_network_providers.transactions import TransactionOnNetwork

from mxops.config.config import Config
from mxops.data.execution_data import InternalContractData, ScenarioData, TokenData
from mxops.enums import TokenTypeEnum
from mxops.execution import token_management_builders, utils
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

    def _create_builder(self) -> tx_builder.TransactionBuilder:
        """
        Interface for the method that will create the transaction builder

        :return: builder for the transaction to send
        :rtype: TransactionBuilder
        """
        raise NotImplementedError

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
        sender_account = AccountsManager.get_account(self.sender)
        builder = self._create_builder()
        tx = builder.build()
        tx.nonce = sender_account.nonce
        tx.signature = sender_account.signer.sign(tx)
        sender_account.nonce += 1

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
    upgradeable: bool = True
    readable: bool = True
    payable: bool = False
    payable_by_sc: bool = False
    arguments: List = field(default_factory=list)

    def _create_builder(self) -> tx_builder.TransactionBuilder:
        """
        Create the builder for the contract deployment transaction

        :return: builder of the transaction
        :rtype: tx_builder.TransactionBuilder
        """
        LOGGER.info(f"Deploying contract {self.contract_id}")
        scenario_data = ScenarioData.get()

        # check that the id of the contract is free
        try:
            scenario_data.get_contract_value(self.contract_id, "address")
            raise errors.ContractIdAlreadyExists(self.contract_id)
        except errors.UnknownContract:
            pass

        metadata = CodeMetadata(
            self.upgradeable, self.readable, self.payable, self.payable_by_sc
        )
        args = utils.retrieve_and_format_arguments(self.arguments)

        builder = tx_builder.ContractDeploymentBuilder(
            config=token_management_builders.get_builder_config(),
            owner=utils.get_address_instance(self.sender),
            deploy_arguments=args,
            code_metadata=metadata,
            code=Path(self.wasm_path).read_bytes(),
            gas_limit=self.gas_limit,
        )
        return builder

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

        contract_data = InternalContractData(
            contract_id=self.contract_id,
            address=contract_address.bech32(),
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

    sender: Dict
    contract: str
    wasm_path: str
    gas_limit: int
    upgradeable: bool = True
    readable: bool = True
    payable: bool = False
    payable_by_sc: bool = False
    arguments: List = field(default_factory=lambda: [])

    def _create_builder(self) -> tx_builder.TransactionBuilder:
        """
        Create the builder for the contract upgrade transaction

        :return: builder of the transaction
        :rtype: tx_builder.TransactionBuilder
        """
        LOGGER.info(f"Upgrading contract {self.contract}")

        metadata = CodeMetadata(
            self.upgradeable, self.readable, self.payable, self.payable_by_sc
        )
        args = utils.retrieve_and_format_arguments(self.arguments)

        builder = tx_builder.ContractUpgradeBuilder(
            config=token_management_builders.get_builder_config(),
            contract=utils.get_address_instance(self.contract),
            owner=utils.get_address_instance(self.sender),
            upgrade_arguments=args,
            code_metadata=metadata,
            code=Path(self.wasm_path).read_bytes(),
            gas_limit=self.gas_limit,
        )
        return builder

    def _post_transaction_execution(self, on_chain_tx: TransactionOnNetwork | None):
        """
        Save the new contract data in the Scenario

        :param on_chain_tx: successful upgrade transaction
        :type on_chain_tx: TransactionOnNetwork | None
        """
        if not isinstance(on_chain_tx, TransactionOnNetwork):
            raise ValueError("On chain transaction is None")

        scenario_data = ScenarioData.get()
        try:
            scenario_data.set_contract_value(
                self.contract, "last_upgrade_time", on_chain_tx.timestamp
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

    def _create_builder(self) -> tx_builder.TransactionBuilder:
        """
        Create the builder for the contract upgrade transaction

        :return: builder of the transaction
        :rtype: tx_builder.TransactionBuilder
        """
        LOGGER.info(f"Calling {self.endpoint} for {self.contract}")

        args = utils.retrieve_and_format_arguments(self.arguments)
        esdt_transfers = [
            TokenPayment.meta_esdt_from_integer(
                utils.retrieve_value_from_string(trf.token_identifier),
                utils.retrieve_value_from_any(trf.nonce),
                utils.retrieve_value_from_any(trf.amount),
                0,
            )
            for trf in self.esdt_transfers
        ]
        value = utils.retrieve_value_from_any(self.value)

        builder = tx_builder.ContractCallBuilder(
            config=token_management_builders.get_builder_config(),
            contract=utils.get_address_instance(self.contract),
            caller=utils.get_address_instance(self.sender),
            function_name=self.endpoint,
            value=value,
            call_arguments=args,
            esdt_transfers=esdt_transfers,
            gas_limit=self.gas_limit,
        )
        return builder

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

    def _interpret_return_data(self, data: str) -> QueryResult:
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

    def execute(self):
        """
        Execute a query and optionally save the result
        """
        LOGGER.info(f"Query on {self.endpoint} for {self.contract}")
        config = Config.get_config()
        scenario_data = ScenarioData.get()
        args = utils.retrieve_and_format_arguments(self.arguments)
        builder = ContractQueryBuilder(
            contract=utils.get_address_instance(self.contract),
            function=self.endpoint,
            call_arguments=args,
        )
        query = builder.build()
        proxy = ProxyNetworkProvider(config.get("PROXY"))

        results_empty = True
        n_attempts = 0
        max_attempts = int(Config.get_config().get("MAX_QUERY_ATTEMPTS"))
        while results_empty and n_attempts < max_attempts:
            n_attempts += 1
            response = proxy.query_contract(query)
            self.results = [
                self._interpret_return_data(data) for data in response.return_data
            ]
            results_empty = len(self.results) == 0 or (
                len(self.results) == 1 and self.results[0] == ""
            )
            if results_empty:
                time.sleep(3)
                LOGGER.warning(
                    f"Empty query result, retrying. Attempt {n_attempts}/{max_attempts}"
                )
        if results_empty:
            raise errors.EmptyQueryResults
        if self.print_results:
            print(self.results)
        if len(self.expected_results) > 0:
            LOGGER.info("Saving Query results as contract data")
            for result, expected_result in zip(self.results, self.expected_results):
                parsed_result = parse_query_result(
                    result, expected_result["result_type"]
                )
                scenario_data.set_contract_value(
                    self.contract, expected_result["save_key"], parsed_result
                )
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

    def _create_builder(self) -> tx_builder.TransactionBuilder:
        """
        Create the builder for the fungible issue transaction

        :return: builder for the transaction
        :rtype: tx_builder.TransactionBuilder
        """
        LOGGER.info(
            f"Issuing fungible token named {self.token_name} "
            f"for the account {self.sender}"
        )
        builder = token_management_builders.FungibleTokenIssueBuilder(
            config=token_management_builders.get_builder_config(),
            issuer=utils.get_address_instance(self.sender),
            token_name=self.token_name,
            token_ticker=self.token_ticker,
            initial_supply=self.initial_supply,
            num_decimals=self.num_decimals,
            can_freeze=self.can_freeze,
            can_wipe=self.can_wipe,
            can_pause=self.can_pause,
            can_mint=self.can_mint,
            can_burn=self.can_burn,
            can_change_owner=self.can_change_owner,
            can_upgrade=self.can_upgrade,
            can_add_special_roles=self.can_add_special_roles,
        )
        return builder

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

    def _create_builder(self) -> tx_builder.TransactionBuilder:
        """
        Create the builder for the non fungible issue transaction

        :return: builder for the transaction
        :rtype: tx_builder.TransactionBuilder
        """
        LOGGER.info(
            f"Issuing non fungible token named {self.token_name} "
            f"for the account {self.sender}"
        )
        builder = token_management_builders.NonFungibleTokenIssueBuilder(
            config=token_management_builders.get_builder_config(),
            issuer=utils.get_address_instance(self.sender),
            token_name=self.token_name,
            token_ticker=self.token_ticker,
            can_freeze=self.can_freeze,
            can_wipe=self.can_wipe,
            can_pause=self.can_pause,
            can_change_owner=self.can_change_owner,
            can_upgrade=self.can_upgrade,
            can_add_special_roles=self.can_add_special_roles,
            can_transfer_nft_create_role=self.can_add_special_roles,
        )
        return builder

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

    def _create_builder(self) -> tx_builder.TransactionBuilder:
        """
        Create the builder for the semi fungible issue transaction

        :return: builder for the transaction
        :rtype: tx_builder.TransactionBuilder
        """
        LOGGER.info(
            f"Issuing semi fungible token named {self.token_name} "
            f"for the account {self.sender}"
        )
        builder = token_management_builders.SemiFungibleTokenIssueBuilder(
            config=token_management_builders.get_builder_config(),
            issuer=utils.get_address_instance(self.sender),
            token_name=self.token_name,
            token_ticker=self.token_ticker,
            can_freeze=self.can_freeze,
            can_wipe=self.can_wipe,
            can_pause=self.can_pause,
            can_change_owner=self.can_change_owner,
            can_upgrade=self.can_upgrade,
            can_add_special_roles=self.can_add_special_roles,
            can_transfer_nft_create_role=self.can_transfer_nft_create_role,
        )
        return builder

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

    def _create_builder(self) -> tx_builder.TransactionBuilder:
        """
        Create the builder for the meta issue transaction

        :return: builder for the transaction
        :rtype: tx_builder.TransactionBuilder
        """
        LOGGER.info(
            f"Issuing meta token named {self.token_name} "
            f"for the account {self.sender}"
        )
        builder = token_management_builders.MetaFungibleTokenIssueBuilder(
            config=token_management_builders.get_builder_config(),
            issuer=utils.get_address_instance(self.sender),
            token_name=self.token_name,
            token_ticker=self.token_ticker,
            num_decimals=self.num_decimals,
            can_freeze=self.can_freeze,
            can_wipe=self.can_wipe,
            can_pause=self.can_pause,
            can_change_owner=self.can_change_owner,
            can_upgrade=self.can_upgrade,
            can_add_special_roles=self.can_add_special_roles,
            can_transfer_nft_create_role=self.can_transfer_nft_create_role,
        )
        return builder

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

    def _create_builder(self) -> tx_builder.TransactionBuilder:
        """
        Create the builder for the manage token roles transaction

        :return: builder for the transaction
        :rtype: tx_builder.TransactionBuilder
        """
        token_identifier = utils.retrieve_value_from_string(self.token_identifier)
        target = utils.get_address_instance(self.target)
        LOGGER.info(
            f"Setting roles {self.roles} on the token {self.token_identifier}"
            f" ({token_identifier}) for {self.target} ({target})"
        )

        builder = token_management_builders.ManageTokenRolesBuilder(
            config=token_management_builders.get_builder_config(),
            sender=utils.get_address_instance(self.sender),
            is_set=self.is_set,
            token_identifier=token_identifier,
            target=target,
            roles=utils.retrieve_values_from_strings(self.roles),
        )
        return builder

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

    def _create_builder(self) -> tx_builder.TransactionBuilder:
        """
        Create the builder for the fungible mint transaction

        :return: builder for the transaction
        :rtype: tx_builder.TransactionBuilder
        """
        token_identifier = utils.retrieve_value_from_string(self.token_identifier)
        amount = utils.retrieve_value_from_any(self.amount)
        LOGGER.info(
            f"Minting additional supply of {amount} ({self.amount}) for the token "
            f" {token_identifier} ({self.token_identifier})"
        )
        builder = token_management_builders.FungibleMintBuilder(
            config=token_management_builders.get_builder_config(),
            sender=utils.get_address_instance(self.sender),
            token_identifier=token_identifier,
            amount_as_integer=amount,
        )
        return builder


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

    def _create_builder(self) -> tx_builder.TransactionBuilder:
        """
        Create the builder for the meta issue transaction

        :return: builder for the transaction
        :rtype: tx_builder.TransactionBuilder
        """
        token_identifier = utils.retrieve_value_from_string(self.token_identifier)
        amount = utils.retrieve_value_from_any(self.amount)
        LOGGER.info(
            f"Minting new nonce with a supply of {amount} ({self.amount}) for the token"
            f" {token_identifier} ({self.token_identifier})"
        )
        builder = token_management_builders.NonFungibleMintBuilder(
            config=token_management_builders.get_builder_config(),
            sender=utils.get_address_instance(self.sender),
            token_identifier=token_identifier,
            amount_as_integer=amount,
            name=utils.retrieve_value_from_string(self.name),
            royalties=utils.retrieve_value_from_any(self.royalties),
            hash=utils.retrieve_value_from_string(self.hash),
            attributes=utils.retrieve_value_from_string(self.attributes),
            uris=utils.retrieve_values_from_strings(self.uris),
        )
        return builder

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

    def _create_builder(self) -> tx_builder.TransactionBuilder:
        """
        Create the builder for the egld transfer transaction

        :return: builder of the transaction
        :rtype: tx_builder.TransactionBuilder
        """
        amount = int(utils.retrieve_value_from_any(self.amount))
        payment = TokenPayment.egld_from_integer(amount)

        builder = tx_builder.EGLDTransferBuilder(
            config=token_management_builders.get_builder_config(),
            sender=utils.get_address_instance(self.sender),
            receiver=utils.get_address_instance(self.receiver),
            payment=payment,
        )

        LOGGER.info(f"Sending {amount} eGLD from {self.sender} to {self.receiver}")
        return builder


@dataclass
class FungibleTransferStep(TransactionStep):
    """
    This step is used to transfer some fungible ESDT to an address
    """

    receiver: str
    token_identifier: str
    amount: Union[str, int]

    def _create_builder(self) -> tx_builder.TransactionBuilder:
        """
        Create the builder for the ESDT transfer transaction

        :return: builder of the transaction
        :rtype: tx_builder.TransactionBuilder
        """
        token_identifier = utils.retrieve_value_from_string(self.token_identifier)
        amount = int(utils.retrieve_value_from_any(self.amount))
        payment = TokenPayment.fungible_from_integer(token_identifier, amount, 0)

        builder = tx_builder.ESDTTransferBuilder(
            config=token_management_builders.get_builder_config(),
            sender=utils.get_address_instance(self.sender),
            receiver=utils.get_address_instance(self.receiver),
            payment=payment,
        )

        LOGGER.info(
            f"Sending {amount} {token_identifier} from {self.sender} to {self.receiver}"
        )
        return builder


@dataclass
class NonFungibleTransferStep(TransactionStep):
    """
    This step is used to transfer some non fungible ESDT to an address
    """

    receiver: str
    token_identifier: str
    nonce: Union[str, int]
    amount: Union[str, int]

    def _create_builder(self) -> tx_builder.TransactionBuilder:
        """
        Create the builder for the NFT transfer transaction

        :return: builder of the transaction
        :rtype: tx_builder.TransactionBuilder
        """
        token_identifier = utils.retrieve_value_from_string(self.token_identifier)
        nonce = int(utils.retrieve_value_from_any(self.nonce))
        amount = int(utils.retrieve_value_from_any(self.amount))
        payment = TokenPayment.meta_esdt_from_integer(
            token_identifier, nonce, amount, 0
        )

        builder = tx_builder.ESDTNFTTransferBuilder(
            config=token_management_builders.get_builder_config(),
            sender=utils.get_address_instance(self.sender),
            destination=utils.get_address_instance(self.receiver),
            payment=payment,
        )

        LOGGER.info(
            f"Sending {amount} {token_identifier}-{arg_to_string(nonce)} "
            f"from {self.sender} to {self.receiver}"
        )
        return builder


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

    def _create_builder(self) -> tx_builder.TransactionBuilder:
        """
        Create the builder for the multi transfer transaction

        :return: builder of the transaction
        :rtype: tx_builder.TransactionBuilder
        """
        payments = [
            TokenPayment.meta_esdt_from_integer(
                utils.retrieve_value_from_string(transfer.token_identifier),
                int(utils.retrieve_value_from_any(transfer.nonce)),
                int(utils.retrieve_value_from_any(transfer.amount)),
                0,
            )
            for transfer in self.transfers
        ]

        builder = tx_builder.MultiESDTNFTTransferBuilder(
            config=token_management_builders.get_builder_config(),
            sender=utils.get_address_instance(self.sender),
            destination=utils.get_address_instance(self.receiver),
            payments=payments,
        )

        LOGGER.info(f"Sending multiple payments from {self.sender} to {self.receiver}")
        return builder


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
        arguments = [utils.retrieve_value_from_any(arg) for arg in self.arguments]
        keyword_arguments = {
            key: utils.retrieve_value_from_any(val)
            for key, val in self.keyword_arguments.items()
        }
        result = user_function(*arguments, **keyword_arguments)

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
