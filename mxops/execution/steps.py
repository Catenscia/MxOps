"""
author: Etienne Wallet

This module contains the classes used to execute scenes in a scenario
"""
from dataclasses import dataclass, field
import os
from pathlib import Path
import sys
from typing import ClassVar, Dict, List, Set, Union

from multiversx_sdk_cli.contracts import CodeMetadata
from multiversx_sdk_core import Address, TokenPayment
from multiversx_sdk_core import transaction_builders as tx_builder
from multiversx_sdk_core.serializer import arg_to_string

from mxops.config.config import Config
from mxops.data.data import InternalContractData, ScenarioData, TokenData
from mxops.enums import TokenTypeEnum
from mxops.execution import token_management_builders, utils
from mxops.execution.account import AccountsManager
from mxops.execution import contract_interactions as cti
from mxops.execution import token_management as tkm
from mxops.execution.checks import Check, SuccessCheck, instanciate_checks
from mxops.execution.msc import EsdtTransfer
from mxops.execution.network import raise_on_errors, send, send_and_wait_for_result
from mxops.execution.utils import parse_query_result
from mxops.utils.logger import get_logger
from mxops.utils.msc import get_file_hash, get_tx_link
from mxops import errors

LOGGER = get_logger('steps')


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

    def execute(self):
        """
        Execute in loop the inner steps
        """
        if self.var_start is not None and self.var_end is not None:
            iterator = range(self.var_start, self.var_end)
        elif self.var_list is not None:
            iterator = self.var_list
        else:
            raise ValueError('Loop iteration is not correctly defined')
        for var in iterator:
            os.environ[self.var_name] = str(var)
            for step in self.steps:
                step.execute()

    def __post_init__(self):
        """
        After the initialisation of an instance, if the inner steps are
        found to be Dict, will try to convert them to Steps instances.
        Usefull for easy loading from yaml files
        """
        if len(self.steps) > 0 and isinstance(self.steps[0], Dict):
            self.steps = instanciate_steps(self.steps)


@dataclass
class ContractDeployStep(Step):
    """
    Represents a smart contract deployment
    """
    sender: Dict
    wasm_path: str
    contract_id: str
    gas_limit: int
    upgradeable: bool = True
    readable: bool = True
    payable: bool = False
    payable_by_sc: bool = False
    arguments: List = field(default_factory=lambda: [])

    def execute(self):
        """
        Execute a contract deployment
        """
        LOGGER.info(f'Deploying contract {self.contract_id}')
        scenario_data = ScenarioData.get()

        # check that the id of the contract is free
        try:
            scenario_data.get_contract_value(self.contract_id, 'address')
            raise errors.ContractIdAlreadyExists(self.contract_id)
        except errors.UnknownContract:
            pass

        # contruct the transaction
        sender = AccountsManager.get_account(self.sender)
        metadata = CodeMetadata(self.upgradeable, self.readable,
                                self.payable, self.payable_by_sc)
        wasm_path = Path(self.wasm_path)
        tx, contract = cti.get_contract_deploy_tx(wasm_path, metadata,
                                                  self.gas_limit, self.arguments, sender)
        on_chain_tx = send_and_wait_for_result(tx)
        raise_on_errors(on_chain_tx)
        sender.nonce += 1
        LOGGER.info((f'Deploy successful on {contract.address}'
                     f'\ntx hash: {get_tx_link(on_chain_tx.hash)}'))

        creation_timestamp = on_chain_tx.to_dictionary()['timestamp']
        contract_data = InternalContractData(
            contract_id=self.contract_id,
            address=contract.address.bech32(),
            saved_values={},
            wasm_hash=get_file_hash(wasm_path),
            deploy_time=creation_timestamp,
            last_upgrade_time=creation_timestamp,
        )
        scenario_data.add_contract_data(contract_data)


@dataclass
class ContractCallStep(Step):
    """
    Represents a smart contract endpoint call
    """
    sender: Dict
    contract: str
    endpoint: str
    gas_limit: int
    arguments: List = field(default_factory=lambda: [])
    value: int = 0
    esdt_transfers: List[EsdtTransfer] = field(default_factory=lambda: [])
    checks: List[Check] = field(default_factory=lambda: [SuccessCheck()])

    def __post_init__(self):
        """
        After the initialisation of an instance, if the esdt transfers are
        found to be Dict,
        will try to convert them to EsdtTransfers instances.
        Usefull for easy loading from yaml files
        """
        checked_transfers = []
        for trf in self.esdt_transfers:
            if isinstance(trf, EsdtTransfer):
                checked_transfers.append(trf)
            elif isinstance(trf, Dict):
                checked_transfers.append(EsdtTransfer(**trf))
            else:
                raise ValueError(f'Unexpected type: {type(trf)}')
        self.esdt_transfers = checked_transfers

        if len(self.checks) > 0 and isinstance(self.checks[0], Dict):
            self.checks = instanciate_checks(self.checks)

    def execute(self):
        """
        Execute a contract call
        """
        LOGGER.info(f'Calling {self.endpoint} for {self.contract}')
        sender = AccountsManager.get_account(self.sender)

        tx = cti.get_contract_call_tx(self.contract,
                                      self.endpoint,
                                      self.gas_limit,
                                      self.arguments,
                                      self.value,
                                      self.esdt_transfers,
                                      sender)

        if self.checks:
            on_chain_tx = send_and_wait_for_result(tx)
            for check in self.checks:
                check.raise_on_failure(on_chain_tx)
            LOGGER.info(
                f'Call successful: {get_tx_link(on_chain_tx.hash)}')
        else:
            tx_hash = send(tx)
            LOGGER.info(f'Call sent: {get_tx_link(tx_hash)}')
        sender.nonce += 1


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

    def execute(self):
        """
        Execute a query and optionally save the result
        """
        LOGGER.info(f'Query on {self.endpoint} for {self.contract}')
        scenario_data = ScenarioData.get()
        results = cti.query_contract(self.contract,
                                     self.endpoint,
                                     self.arguments)

        if self.print_results:
            print(results)

        if len(results) == 0 or (len(results) == 1 and results[0] == ''):
            raise errors.EmptyQueryResults
        if len(self.expected_results) > 0:
            LOGGER.info('Saving Query results as contract data')
            for result, expected_result in zip(results, self.expected_results):
                parsed_result = parse_query_result(result,
                                                   expected_result['result_type'])
                scenario_data.set_contract_value(self.contract,
                                                 expected_result['save_key'],
                                                 parsed_result)
        LOGGER.info('Query successful')


@dataclass
class FungibleIssueStep(Step):
    """
    Represents the issuance of a fungible token
    """
    sender: str
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

    def execute(self):
        """
        Execute a fungible token issuance and save the token identifier of the created token
        """
        LOGGER.info(f'Issuing fungible token named {self.token_name} for the account {self.sender}')
        scenario_data = ScenarioData.get()
        sender = AccountsManager.get_account(self.sender)

        tx = tkm.build_fungible_issue_tx(
            sender,
            self.token_name,
            self.token_ticker,
            self.initial_supply,
            self.num_decimals,
            self.can_freeze,
            self.can_wipe,
            self.can_pause,
            self.can_mint,
            self.can_change_owner,
            self.can_upgrade,
            self.can_add_special_roles
        )
        on_chain_tx = send_and_wait_for_result(tx)
        raise_on_errors(on_chain_tx)
        sender.nonce += 1
        LOGGER.info(f'Call successful: {get_tx_link(on_chain_tx.hash)}')

        token_identifier = tkm.extract_new_token_identifier(on_chain_tx)
        LOGGER.info(f'Newly issued token got the identifier {token_identifier}')
        scenario_data.add_token_data(TokenData(
            name=self.token_name,
            ticker=self.token_ticker,
            identifier=token_identifier,
            saved_values={},
            type=TokenTypeEnum.FUNGIBLE
        ))


@dataclass
class NonFungibleIssueStep(Step):
    """
    Represents the issuance of a non fungible token
    """
    sender: str
    token_name: str
    token_ticker: str
    can_freeze: bool = False
    can_wipe: bool = False
    can_pause: bool = False
    can_mint: bool = False
    can_burn: bool = False
    can_change_owner: bool = False
    can_upgrade: bool = False
    can_add_special_roles: bool = False
    can_transfer_nft_create_role: bool = False

    def execute(self):
        """
        Execute a non fungible token issuance and save the token identifier of the created token
        """
        LOGGER.info(
            f'Issuing non fungible token named {self.token_name} for the account {self.sender}'
        )
        scenario_data = ScenarioData.get()
        sender = AccountsManager.get_account(self.sender)

        tx = tkm.build_non_fungible_issue_tx(
            sender,
            self.token_name,
            self.token_ticker,
            self.can_freeze,
            self.can_wipe,
            self.can_pause,
            self.can_mint,
            self.can_change_owner,
            self.can_upgrade,
            self.can_add_special_roles,
            self.can_transfer_nft_create_role
        )
        on_chain_tx = send_and_wait_for_result(tx)
        raise_on_errors(on_chain_tx)
        sender.nonce += 1
        LOGGER.info(f'Call successful: {get_tx_link(on_chain_tx.hash)}')

        token_identifier = tkm.extract_new_token_identifier(on_chain_tx)
        LOGGER.info(f'Newly issued token got the identifier {token_identifier}')
        scenario_data.add_token_data(TokenData(
            name=self.token_name,
            ticker=self.token_ticker,
            identifier=token_identifier,
            saved_values={},
            type=TokenTypeEnum.NON_FUNGIBLE
        ))


@dataclass
class SemiFungibleIssueStep(Step):
    """
    Represents the issuance of a semi fungible token
    """
    sender: str
    token_name: str
    token_ticker: str
    can_freeze: bool = False
    can_wipe: bool = False
    can_pause: bool = False
    can_mint: bool = False
    can_burn: bool = False
    can_change_owner: bool = False
    can_upgrade: bool = False
    can_add_special_roles: bool = False
    can_transfer_nft_create_role: bool = False

    def execute(self):
        """
        Execute a semi fungible token issuance and save the token identifier of the created token
        """
        LOGGER.info(
            f'Issuing semi fungible token named {self.token_name} for the account {self.sender}'
        )
        scenario_data = ScenarioData.get()
        sender = AccountsManager.get_account(self.sender)

        tx = tkm.build_semi_fungible_issue_tx(
            sender,
            self.token_name,
            self.token_ticker,
            self.can_freeze,
            self.can_wipe,
            self.can_pause,
            self.can_mint,
            self.can_change_owner,
            self.can_upgrade,
            self.can_add_special_roles,
            self.can_transfer_nft_create_role
        )
        on_chain_tx = send_and_wait_for_result(tx)
        raise_on_errors(on_chain_tx)
        sender.nonce += 1
        LOGGER.info(f'Call successful: {get_tx_link(on_chain_tx.hash)}')

        token_identifier = tkm.extract_new_token_identifier(on_chain_tx)
        LOGGER.info(f'Newly issued token got the identifier {token_identifier}')
        scenario_data.add_token_data(TokenData(
            name=self.token_name,
            ticker=self.token_ticker,
            identifier=token_identifier,
            saved_values={},
            type=TokenTypeEnum.SEMI_FUNGIBLE
        ))


@dataclass
class MetaIssueStep(Step):
    """
    Represents the issuance of a meta fungible token
    """
    sender: str
    token_name: str
    token_ticker: str
    num_decimals: int
    can_freeze: bool = False
    can_wipe: bool = False
    can_pause: bool = False
    can_mint: bool = False
    can_burn: bool = False
    can_change_owner: bool = False
    can_upgrade: bool = False
    can_add_special_roles: bool = False
    can_transfer_nft_create_role: bool = False

    def execute(self):
        """
        Execute a meta token issuance and save the token identifier of the created token
        """
        LOGGER.info(
            f'Issuing meta fungible token named {self.token_name} for the account {self.sender}'
        )
        scenario_data = ScenarioData.get()
        sender = AccountsManager.get_account(self.sender)

        tx = tkm.build_meta_issue_tx(
            sender,
            self.token_name,
            self.token_ticker,
            self.num_decimals,
            self.can_freeze,
            self.can_wipe,
            self.can_pause,
            self.can_mint,
            self.can_change_owner,
            self.can_upgrade,
            self.can_add_special_roles,
            self.can_transfer_nft_create_role
        )
        on_chain_tx = send_and_wait_for_result(tx)
        raise_on_errors(on_chain_tx)
        sender.nonce += 1
        LOGGER.info(f'Call successful: {get_tx_link(on_chain_tx.hash)}')

        token_identifier = tkm.extract_new_token_identifier(on_chain_tx)
        LOGGER.info(f'Newly issued token got the identifier {token_identifier}')
        scenario_data.add_token_data(TokenData(
            name=self.token_name,
            ticker=self.token_ticker,
            identifier=token_identifier,
            saved_values={},
            type=TokenTypeEnum.SEMI_FUNGIBLE
        ))


@dataclass
class ManageTokenRolesStep(Step):
    """
    A base step to set or unset roles on a token.
    Can not be used on its own: on must use the child classes
    """
    sender: str
    is_set: bool
    token_identifier: str
    target: str
    roles: List[str]
    ALLOWED_ROLES: ClassVar[Set] = set()

    def execute(self):
        """
        Execute a transaction to manage the roles of an address on a token
        """

        config = Config.get_config()
        builder_config = token_management_builders.MyDefaultTransactionBuildersConfiguration(
            chain_id=config.get('CHAIN')
        )

        sender = AccountsManager.get_account(self.sender)
        token_identifier = utils.retrieve_value_from_string(self.token_identifier)
        roles = utils.retrieve_values_from_strings(self.roles)
        target = Address.from_bech32(utils.retrieve_value_from_string(self.target))

        LOGGER.info(f'Setting roles {self.roles} on the token {token_identifier}'
                    f' ({self.token_identifier}) for the address {target} ({self.target})'
                    )

        builder = token_management_builders.ManageTokenRolesBuilder(
            builder_config,
            sender.address,
            self.is_set,
            token_identifier,
            target,
            roles,
            nonce=sender.nonce
        )
        tx = builder.build()
        tx.signature = sender.signer.sign(tx)
        sender.nonce += 1

        on_chain_tx = send_and_wait_for_result(tx)
        raise_on_errors(on_chain_tx)
        LOGGER.info(f'Call successful: {get_tx_link(on_chain_tx.hash)}')

    def __post_init__(self):
        for role in self.roles:
            if role not in self.ALLOWED_ROLES:
                raise ValueError(f'role {role} is not in allowed roles {self.ALLOWED_ROLES}')


@dataclass
class ManageFungibleTokenRolesStep(ManageTokenRolesStep):
    """
    This step is used to set or unset roles for an adress on a fungible token
    """
    ALLOWED_ROLES: ClassVar[Set] = {
        'ESDTRoleLocalBurn',
        'ESDTRoleLocalMint',
        'ESDTTransferRole'
    }


@dataclass
class ManageNonFungibleTokenRolesStep(ManageTokenRolesStep):
    """
    This step is used to set or unset roles for an adress on a non fungible token
    """
    ALLOWED_ROLES: ClassVar[Set] = {
        'ESDTRoleNFTCreate',
        'ESDTRoleNFTBurn',
        'ESDTRoleNFTUpdateAttributes',
        'ESDTRoleNFTAddURI',
        'ESDTTransferRole'
    }


@dataclass
class ManageSemiFungibleTokenRolesStep(ManageTokenRolesStep):
    """
    This step is used to set or unset roles for an adress on a semi fungible token
    """
    ALLOWED_ROLES: ClassVar[Set] = {
        'ESDTRoleNFTCreate',
        'ESDTRoleNFTBurn',
        'ESDTRoleNFTAddQuantity',
        'ESDTTransferRole'
    }


@dataclass
class ManageMetaTokenRolesStep(ManageSemiFungibleTokenRolesStep):
    """
    This step is used to set or unset roles for an adress on a meta token
    """


@dataclass
class FungibleMintStep(Step):
    """
    This step is used to mint an additional supply for an already existing fungible token
    """
    sender: str
    token_identifier: str
    amount: Union[str, int]

    def execute(self):
        """
        Execute a transaction to mint an additional supply for an already existing fungible token
        """
        config = Config.get_config()
        builder_config = token_management_builders.MyDefaultTransactionBuildersConfiguration(
            chain_id=config.get('CHAIN')
        )

        sender = AccountsManager.get_account(self.sender)
        token_identifier = utils.retrieve_value_from_string(self.token_identifier)
        amount = utils.retrieve_value_from_any(self.amount)

        LOGGER.info(
            f'Minting additional supply of {amount} ({self.amount}) for the token '
            f' {token_identifier} ({self.token_identifier})'
        )

        builder = token_management_builders.FungibleMintBuilder(
            builder_config,
            sender.address,
            token_identifier,
            amount,
            nonce=sender.nonce
        )
        tx = builder.build()
        tx.signature = sender.signer.sign(tx)
        sender.nonce += 1

        on_chain_tx = send_and_wait_for_result(tx)
        raise_on_errors(on_chain_tx)
        LOGGER.info(f'Call successful: {get_tx_link(on_chain_tx.hash)}')


@dataclass
class NonFungibleMintStep(Step):
    """
    This step is used to mint a new nonce for an already existing non fungible token.
    It can be used for NFTs, SFTs and Meta tokens.
    """
    sender: str
    token_identifier: str
    amount: Union[str, int]
    name: str = ''
    royalties: Union[str, int] = 0
    hash: str = ''
    attributes: str = ''
    uris: List[str] = field(default_factory=lambda: [])

    def execute(self):
        """
        Execute a transaction to mint a new nonce for an already existing non fungible token
        """
        config = Config.get_config()
        builder_config = token_management_builders.MyDefaultTransactionBuildersConfiguration(
            chain_id=config.get('CHAIN')
        )

        sender = AccountsManager.get_account(self.sender)
        token_identifier = utils.retrieve_value_from_string(self.token_identifier)
        amount = utils.retrieve_value_from_any(self.amount)

        LOGGER.info(
            f'Minting new nonce with a supply of {amount} ({self.amount}) for the token '
            f' {token_identifier} ({self.token_identifier})'
        )

        builder = token_management_builders.NonFungibleMintBuilder(
            builder_config,
            sender.address,
            token_identifier,
            amount,
            utils.retrieve_value_from_string(self.name),
            utils.retrieve_value_from_any(self.royalties),
            utils.retrieve_value_from_string(self.hash),
            utils.retrieve_value_from_string(self.attributes),
            utils.retrieve_values_from_strings(self.uris),
            nonce=sender.nonce
        )
        tx = builder.build()
        tx.signature = sender.signer.sign(tx)
        sender.nonce += 1

        on_chain_tx = send_and_wait_for_result(tx)
        raise_on_errors(on_chain_tx)
        LOGGER.info(f'Call successful: {get_tx_link(on_chain_tx.hash)}')

        new_nonce = tkm.extract_new_nonce(on_chain_tx)
        LOGGER.info(f'Newly issued nonce is {new_nonce}')


@dataclass
class EgldTransferStep(Step):
    """
    This step is used to transfer some eGLD to an address
    """
    sender: str
    receiver: str
    amount: Union[str, int]
    check_success: bool = True

    def execute(self):
        """
        Execute an eGLD transfer transaction
        """
        config = Config.get_config()
        builder_config = token_management_builders.MyDefaultTransactionBuildersConfiguration(
            chain_id=config.get('CHAIN')
        )

        sender = AccountsManager.get_account(self.sender)
        receiver_address = utils.get_address_instance(self.receiver)
        amount = int(utils.retrieve_value_from_any(self.amount))
        payment = TokenPayment.egld_from_integer(amount)

        LOGGER.info(f'Sending {amount} eGLD from {self.sender} to {self.receiver}')

        builder = tx_builder.EGLDTransferBuilder(
            config=builder_config,
            sender=sender.address,
            receiver=receiver_address,
            payment=payment,
            nonce=sender.nonce
        )

        tx = builder.build()
        tx.signature = sender.signer.sign(tx)
        sender.nonce += 1

        if self.check_success:
            on_chain_tx = send_and_wait_for_result(tx)
            raise_on_errors(on_chain_tx)
            LOGGER.info(f'Transaction successful: {get_tx_link(on_chain_tx.hash)}')
        else:
            send(tx)
            LOGGER.info('Transaction sent')


@dataclass
class FungibleTransferStep(Step):
    """
    This step is used to transfer some fungible ESDT to an address
    """
    sender: str
    receiver: str
    token_identifier: str
    amount: Union[str, int]
    check_success: bool = True

    def execute(self):
        """
        Execute a fungible ESDT transfer transaction
        """
        config = Config.get_config()
        builder_config = token_management_builders.MyDefaultTransactionBuildersConfiguration(
            chain_id=config.get('CHAIN')
        )

        sender = AccountsManager.get_account(self.sender)
        receiver_address = utils.get_address_instance(self.receiver)
        token_identifier = utils.retrieve_value_from_string(self.token_identifier)
        amount = int(utils.retrieve_value_from_any(self.amount))
        payment = TokenPayment.fungible_from_integer(token_identifier, amount, 0)

        LOGGER.info(f'Sending {amount} {token_identifier} from {self.sender} to {self.receiver}')

        builder = tx_builder.ESDTTransferBuilder(
            config=builder_config,
            sender=sender.address,
            receiver=receiver_address,
            payment=payment,
            nonce=sender.nonce
        )

        tx = builder.build()
        tx.signature = sender.signer.sign(tx)
        sender.nonce += 1

        if self.check_success:
            on_chain_tx = send_and_wait_for_result(tx)
            raise_on_errors(on_chain_tx)
            LOGGER.info(f'Transaction successful: {get_tx_link(on_chain_tx.hash)}')
        else:
            send(tx)
            LOGGER.info('Transaction sent')


@dataclass
class NonFungibleTransferStep(Step):
    """
    This step is used to transfer some non fungible ESDT to an address
    """
    sender: str
    receiver: str
    token_identifier: str
    nonce: Union[str, int]
    amount: Union[str, int]
    check_success: bool = True

    def execute(self):
        """
        Execute a fungible ESDT transfer transaction
        """
        config = Config.get_config()
        builder_config = token_management_builders.MyDefaultTransactionBuildersConfiguration(
            chain_id=config.get('CHAIN')
        )

        sender = AccountsManager.get_account(self.sender)
        receiver_address = utils.get_address_instance(self.receiver)
        token_identifier = utils.retrieve_value_from_string(self.token_identifier)
        nonce = int(utils.retrieve_value_from_any(self.nonce))
        amount = int(utils.retrieve_value_from_any(self.amount))
        payment = TokenPayment.meta_esdt_from_integer(token_identifier, nonce, amount, 0)

        LOGGER.info(f'Sending {amount} {token_identifier}-{arg_to_string(nonce)} '
                    f'from {self.sender} to {self.receiver}')

        builder = tx_builder.ESDTNFTTransferBuilder(
            config=builder_config,
            sender=sender.address,
            destination=receiver_address,
            payment=payment,
            nonce=sender.nonce
        )

        tx = builder.build()
        tx.signature = sender.signer.sign(tx)
        sender.nonce += 1

        if self.check_success:
            on_chain_tx = send_and_wait_for_result(tx)
            raise_on_errors(on_chain_tx)
            LOGGER.info(f'Transaction successful: {get_tx_link(on_chain_tx.hash)}')
        else:
            send(tx)
            LOGGER.info('Transaction sent')


@dataclass
class MultiTransfersStep(Step):
    """
    This step is used to transfer multiple ESDTs to an address
    """
    sender: str
    receiver: str
    transfers: List[EsdtTransfer]
    check_success: bool = True

    def __post_init__(self):
        """
        After the initialisation of an instance, if the esdt transfers are
        found to be Dict,
        will try to convert them to EsdtTransfers instances.
        Usefull for easy loading from yaml files
        """
        checked_transfers = []
        for trf in self.transfers:
            if isinstance(trf, EsdtTransfer):
                checked_transfers.append(trf)
            elif isinstance(trf, Dict):
                checked_transfers.append(EsdtTransfer(**trf))
            else:
                raise ValueError(f'Unexpected type: {type(trf)}')
        self.transfers = checked_transfers

    def execute(self):
        """
        Execute a multi ESDT transfers transaction
        """
        config = Config.get_config()
        builder_config = token_management_builders.MyDefaultTransactionBuildersConfiguration(
            chain_id=config.get('CHAIN')
        )

        sender = AccountsManager.get_account(self.sender)
        receiver_address = utils.get_address_instance(self.receiver)

        payments = [
            TokenPayment.meta_esdt_from_integer(
                utils.retrieve_value_from_string(transfer.token_identifier),
                int(utils.retrieve_value_from_any(transfer.nonce)),
                int(utils.retrieve_value_from_any(transfer.amount)),
                0) for transfer in self.transfers
        ]

        LOGGER.info('Sending multiple payments '
                    f'from {self.sender} to {self.receiver}')

        builder = tx_builder.MultiESDTNFTTransferBuilder(
            config=builder_config,
            sender=sender.address,
            destination=receiver_address,
            payments=payments,
            nonce=sender.nonce
        )

        tx = builder.build()
        tx.signature = sender.signer.sign(tx)
        sender.nonce += 1

        if self.check_success:
            on_chain_tx = send_and_wait_for_result(tx)
            raise_on_errors(on_chain_tx)
            LOGGER.info(f'Transaction successful: {get_tx_link(on_chain_tx.hash)}')
        else:
            send(tx)
            LOGGER.info('Transaction sent')


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
        step_type: str = raw_step.pop('type')
        if raw_step.pop('skip', False):
            continue
        step_class_name = step_type if step_type.endswith('Step') else step_type + 'Step'

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
