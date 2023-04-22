"""
author: Etienne Wallet

This module contains the function to manage ESDT
"""
from abc import abstractmethod
import itertools
from typing import Dict, List, Optional

from multiversx_sdk_cli.accounts import Account
from multiversx_sdk_core import Transaction
from multiversx_sdk_core.serializer import args_to_strings
from multiversx_sdk_core.interfaces import (IAddress, IGasLimit, IGasPrice,
                                            INonce, ITransactionValue)
from multiversx_sdk_core.transaction_builders import DefaultTransactionBuildersConfiguration
from multiversx_sdk_core.transaction_builders.transaction_builder import TransactionBuilder
from multiversx_sdk_core.transaction_builders.esdt_builders import IESDTIssueConfiguration
from multiversx_sdk_network_providers.transactions import TransactionOnNetwork

from mxops.config.config import Config
from mxops import errors


class TokenIssueBuilder(TransactionBuilder):
    """
    Base class to construct a token issuance transaction
    """

    def __init__(self,
                 config: IESDTIssueConfiguration,
                 issuer: IAddress,
                 issuance_endpoint: str,
                 nonce: Optional[INonce] = None,
                 value: Optional[ITransactionValue] = None,
                 gas_limit: Optional[IGasLimit] = None,
                 gas_price: Optional[IGasPrice] = None
                 ) -> None:
        super().__init__(config, nonce, value, gas_limit, gas_price)
        self.value = config.issue_cost
        self.gas_limit_esdt_issue = config.gas_limit_esdt_issue

        self.sender = issuer
        self.receiver = config.esdt_contract_address

        self.issuance_endpoint = issuance_endpoint

    def _estimate_execution_gas(self) -> IGasLimit:
        return self.gas_limit_esdt_issue

    @abstractmethod
    def get_token_args(self) -> List:
        pass

    @abstractmethod
    def get_token_properties(self) -> Dict:
        pass

    def get_active_token_properties(self) -> List:
        """
        Return the names of the properties that are active on the token

        :return: names of the active properties
        :rtype: List
        """
        return [prop for prop, value in self.get_token_properties().items() if value]

    def _build_payload_parts(self) -> List[str]:
        properties_args = [(prop, "true") for prop in self.get_active_token_properties()]
        chained_properties_args = list(itertools.chain(*properties_args))
        return [
            self.issuance_endpoint,
            *args_to_strings(self.get_token_args()),
            *args_to_strings(chained_properties_args)
        ]


class FungibleTokenIssueBuilder(TokenIssueBuilder):
    """
    Class to contruct a fungible issuance transaction
    """

    def __init__(self,
                 config: IESDTIssueConfiguration,
                 issuer: IAddress,
                 token_name: str,
                 token_ticker: str,
                 initial_supply: int,
                 num_decimals: int,
                 can_freeze: bool = False,
                 can_wipe: bool = False,
                 can_pause: bool = False,
                 can_mint: bool = False,
                 can_burn: bool = False,
                 can_change_owner: bool = False,
                 can_upgrade: bool = False,
                 can_add_special_roles: bool = False,
                 nonce: Optional[INonce] = None,
                 value: Optional[ITransactionValue] = None,
                 gas_limit: Optional[IGasLimit] = None,
                 gas_price: Optional[IGasPrice] = None
                 ) -> None:
        super().__init__(config, issuer, 'issue', nonce, value, gas_limit, gas_price)

        self.token_name = token_name
        self.token_ticker = token_ticker
        self.initial_supply = initial_supply
        self.num_decimals = num_decimals
        self.can_freeze = can_freeze
        self.can_wipe = can_wipe
        self.can_pause = can_pause
        self.can_mint = can_mint
        self.can_burn = can_burn
        self.can_change_owner = can_change_owner
        self.can_upgrade = can_upgrade
        self.can_add_special_roles = can_add_special_roles

    def get_token_args(self) -> List:
        return [
            self.token_name,
            self.token_ticker,
            self.initial_supply,
            self.num_decimals
        ]

    def get_token_properties(self) -> List:
        return {
            'canFreeze': self.can_freeze,
            'canWipe': self.can_wipe,
            'canPause': self.can_pause,
            'canMint': self.can_mint,
            'canBurn': self.can_burn,
            'canChangeOwner': self.can_change_owner,
            'canUpgrade': self.can_upgrade,
            'canAddSpecialRoles': self.can_add_special_roles
        }


class NonFungibleTokenIssueBuilder(TokenIssueBuilder):
    """
    Class to contruct a non fungible issuance transaction
    """

    def __init__(self,
                 config: IESDTIssueConfiguration,
                 issuer: IAddress,
                 token_name: str,
                 token_ticker: str,
                 can_freeze: bool = False,
                 can_wipe: bool = False,
                 can_pause: bool = False,
                 can_mint: bool = False,
                 can_burn: bool = False,
                 can_change_owner: bool = False,
                 can_upgrade: bool = False,
                 can_add_special_roles: bool = False,
                 can_transfer_nft_create_role: bool = False,
                 nonce: Optional[INonce] = None,
                 value: Optional[ITransactionValue] = None,
                 gas_limit: Optional[IGasLimit] = None,
                 gas_price: Optional[IGasPrice] = None
                 ) -> None:
        super().__init__(config, issuer, 'issueNonFungible', nonce, value, gas_limit, gas_price)

        self.token_name = token_name
        self.token_ticker = token_ticker
        self.can_freeze = can_freeze
        self.can_wipe = can_wipe
        self.can_pause = can_pause
        self.can_mint = can_mint
        self.can_burn = can_burn
        self.can_change_owner = can_change_owner
        self.can_upgrade = can_upgrade
        self.can_add_special_roles = can_add_special_roles
        self.can_transfer_nft_create_role = can_transfer_nft_create_role

    def get_token_args(self) -> List:
        return [
            self.token_name,
            self.token_ticker
        ]

    def get_token_properties(self) -> List:
        return {
            'canFreeze': self.can_freeze,
            'canWipe': self.can_wipe,
            'canPause': self.can_pause,
            'canMint': self.can_mint,
            'canBurn': self.can_burn,
            'canChangeOwner': self.can_change_owner,
            'canUpgrade': self.can_upgrade,
            'canAddSpecialRoles': self.can_add_special_roles,
            'canTransferNFTCreateRole': self.can_transfer_nft_create_role,
        }


class SemiFungibleTokenIssueBuilder(TokenIssueBuilder):
    """
    Class to contruct a semi fungible issuance transaction
    """

    def __init__(self,
                 config: IESDTIssueConfiguration,
                 issuer: IAddress,
                 token_name: str,
                 token_ticker: str,
                 can_freeze: bool = False,
                 can_wipe: bool = False,
                 can_pause: bool = False,
                 can_mint: bool = False,
                 can_burn: bool = False,
                 can_change_owner: bool = False,
                 can_upgrade: bool = False,
                 can_add_special_roles: bool = False,
                 can_transfer_nft_create_role: bool = False,
                 nonce: Optional[INonce] = None,
                 value: Optional[ITransactionValue] = None,
                 gas_limit: Optional[IGasLimit] = None,
                 gas_price: Optional[IGasPrice] = None
                 ) -> None:
        super().__init__(config, issuer, 'issueSemiFungible', nonce, value, gas_limit, gas_price)

        self.token_name = token_name
        self.token_ticker = token_ticker
        self.can_freeze = can_freeze
        self.can_wipe = can_wipe
        self.can_pause = can_pause
        self.can_mint = can_mint
        self.can_burn = can_burn
        self.can_change_owner = can_change_owner
        self.can_upgrade = can_upgrade
        self.can_add_special_roles = can_add_special_roles
        self.can_transfer_nft_create_role = can_transfer_nft_create_role

    def get_token_args(self) -> List:
        return [
            self.token_name,
            self.token_ticker
        ]

    def get_token_properties(self) -> List:
        return {
            'canFreeze': self.can_freeze,
            'canWipe': self.can_wipe,
            'canPause': self.can_pause,
            'canMint': self.can_mint,
            'canBurn': self.can_burn,
            'canChangeOwner': self.can_change_owner,
            'canUpgrade': self.can_upgrade,
            'canAddSpecialRoles': self.can_add_special_roles,
            'canTransferNFTCreateRole': self.can_transfer_nft_create_role,
        }


class MetaFungibleTokenIssueBuilder(TokenIssueBuilder):
    """
    Class to contruct a meta issuance transaction
    """

    def __init__(self,
                 config: IESDTIssueConfiguration,
                 issuer: IAddress,
                 token_name: str,
                 token_ticker: str,
                 num_decimals: int,
                 can_freeze: bool = False,
                 can_wipe: bool = False,
                 can_pause: bool = False,
                 can_mint: bool = False,
                 can_burn: bool = False,
                 can_change_owner: bool = False,
                 can_upgrade: bool = False,
                 can_add_special_roles: bool = False,
                 can_transfer_nft_create_role: bool = False,
                 nonce: Optional[INonce] = None,
                 value: Optional[ITransactionValue] = None,
                 gas_limit: Optional[IGasLimit] = None,
                 gas_price: Optional[IGasPrice] = None
                 ) -> None:
        super().__init__(config, issuer, 'registerMetaESDT', nonce, value, gas_limit, gas_price)

        self.token_name = token_name
        self.token_ticker = token_ticker
        self.num_decimals = num_decimals
        self.can_freeze = can_freeze
        self.can_wipe = can_wipe
        self.can_pause = can_pause
        self.can_mint = can_mint
        self.can_burn = can_burn
        self.can_change_owner = can_change_owner
        self.can_upgrade = can_upgrade
        self.can_add_special_roles = can_add_special_roles
        self.can_transfer_nft_create_role = can_transfer_nft_create_role

    def get_token_args(self) -> List:
        return [
            self.token_name,
            self.token_ticker,
            self.num_decimals
        ]

    def get_token_properties(self) -> List:
        return {
            'canFreeze': self.can_freeze,
            'canWipe': self.can_wipe,
            'canPause': self.can_pause,
            'canMint': self.can_mint,
            'canBurn': self.can_burn,
            'canChangeOwner': self.can_change_owner,
            'canUpgrade': self.can_upgrade,
            'canAddSpecialRoles': self.can_add_special_roles,
            'canTransferNFTCreateRole': self.can_transfer_nft_create_role,
        }


def build_fungible_issue_tx(
    sender: Account,
    token_name: str,
    token_ticker: str,
    initial_supply: int,
    num_decimals: int,
    can_freeze: bool = False,
    can_wipe: bool = False,
    can_pause: bool = False,
    can_mint: bool = False,
    can_burn: bool = False,
    can_change_owner: bool = False,
    can_upgrade: bool = False,
    can_add_special_roles: bool = False
) -> Transaction:
    """
    Build a transaction to issue an ESDT fungible token.

    :param sender: account that will send the transaction
    :type sender: Account
    :param token_name: name if the token to issue
    :type token_name: str
    :param token_ticker: tiocker of the token to issue
    :type token_ticker: str
    :param initial_supply: initial supply that will be sent on the sender account
    :type initial_supply: int
    :param num_decimals: number of decimals of the token
    :type num_decimals: int
    :param can_freeze: if the tokens on specific accounts can be frozen individually,
        defaults to False
    :type can_freeze: bool, optional
    :param can_wipe: if tokens held on frozen accounts can be burnd by the token manager,
        defaults to False
    :type can_wipe: bool, optional
    :param can_pause: if all transactions of the token can be prevented, defaults to False
    :type can_pause: bool, optional
    :param can_mint: if more supply can be minted later on, defaults to False
    :type can_mint: bool, optional
    :param can_burn: if some supply can be burned, defaults to False
    :type can_burn: bool, optional
    :param can_change_owner: if the management of the token can be transfered to another account,
        defaults to False
    :type can_change_owner: bool, optional
    :param can_upgrade: if the properties of the token can be changed by the token manager,
        defaults to False
    :type can_upgrade: bool, optional
    :param can_add_special_roles: if the token manager can add special roles, defaults to False
    :type can_add_special_roles: bool, optional
    :return: the transaction to issue the specified fungible token
    :rtype: Transaction
    """
    config = Config.get_config()
    builder_config = DefaultTransactionBuildersConfiguration(
        chain_id=config.get('CHAIN')
    )

    builder = FungibleTokenIssueBuilder(
        builder_config,
        sender.address,
        token_name,
        token_ticker,
        initial_supply,
        num_decimals,
        can_freeze,
        can_wipe,
        can_pause,
        can_mint,
        can_burn,
        can_change_owner,
        can_upgrade,
        can_add_special_roles,
        nonce=sender.nonce
    )

    tx = builder.build()
    tx.signature = sender.signer.sign(tx)

    return tx


def build_non_fungible_issue_tx(
    sender: Account,
    token_name: str,
    token_ticker: str,
    can_freeze: bool = False,
    can_wipe: bool = False,
    can_pause: bool = False,
    can_mint: bool = False,
    can_burn: bool = False,
    can_change_owner: bool = False,
    can_upgrade: bool = False,
    can_add_special_roles: bool = False,
    can_transfer_nft_create_role: bool = False
) -> Transaction:
    """
    Build a transaction to issue an ESDT fungible token.

    :param sender: account that will send the transaction
    :type sender: Account
    :param token_name: name if the token to issue
    :type token_name: str
    :param token_ticker: tiocker of the token to issue
    :type token_ticker: str
    :param can_freeze: if the tokens on specific accounts can be frozen individually,
        defaults to False
    :type can_freeze: bool, optional
    :param can_wipe: if tokens held on frozen accounts can be burnd by the token manager,
        defaults to False
    :type can_wipe: bool, optional
    :param can_pause: if all transactions of the token can be prevented, defaults to False
    :type can_pause: bool, optional
    :param can_mint: if more supply can be minted later on, defaults to False
    :type can_mint: bool, optional
    :param can_burn: if some supply can be burned, defaults to False
    :type can_burn: bool, optional
    :param can_change_owner: if the management of the token can be transfered to another account,
        defaults to False
    :type can_change_owner: bool, optional
    :param can_upgrade: if the properties of the token can be changed by the token manager,
        defaults to False
    :type can_upgrade: bool, optional
    :param can_add_special_roles: if the token manager can add special roles, defaults to False
    :type can_add_special_roles: bool, optional
    :param can_transfer_nft_create_role: if the token manager transfer the create role,
        defaults to False
    :type can_transfer_nft_create_role: bool, optional
    :return: the transaction to issue the specified fungible token
    :rtype: Transaction
    """
    config = Config.get_config()
    builder_config = DefaultTransactionBuildersConfiguration(
        chain_id=config.get('CHAIN')
    )

    builder = NonFungibleTokenIssueBuilder(
        builder_config,
        sender.address,
        token_name,
        token_ticker,
        can_freeze,
        can_wipe,
        can_pause,
        can_mint,
        can_burn,
        can_change_owner,
        can_upgrade,
        can_add_special_roles,
        can_transfer_nft_create_role,
        nonce=sender.nonce
    )

    tx = builder.build()
    tx.signature = sender.signer.sign(tx)

    return tx


def build_semi_fungible_issue_tx(
    sender: Account,
    token_name: str,
    token_ticker: str,
    can_freeze: bool = False,
    can_wipe: bool = False,
    can_pause: bool = False,
    can_mint: bool = False,
    can_burn: bool = False,
    can_change_owner: bool = False,
    can_upgrade: bool = False,
    can_add_special_roles: bool = False,
    can_transfer_nft_create_role: bool = False
) -> Transaction:
    """
    Build a transaction to issue an ESDT fungible token.

    :param sender: account that will send the transaction
    :type sender: Account
    :param token_name: name if the token to issue
    :type token_name: str
    :param token_ticker: tiocker of the token to issue
    :type token_ticker: str
    :param can_freeze: if the tokens on specific accounts can be frozen individually,
        defaults to False
    :type can_freeze: bool, optional
    :param can_wipe: if tokens held on frozen accounts can be burnd by the token manager,
        defaults to False
    :type can_wipe: bool, optional
    :param can_pause: if all transactions of the token can be prevented, defaults to False
    :type can_pause: bool, optional
    :param can_mint: if more supply can be minted later on, defaults to False
    :type can_mint: bool, optional
    :param can_burn: if some supply can be burned, defaults to False
    :type can_burn: bool, optional
    :param can_change_owner: if the management of the token can be transfered to another account,
        defaults to False
    :type can_change_owner: bool, optional
    :param can_upgrade: if the properties of the token can be changed by the token manager,
        defaults to False
    :type can_upgrade: bool, optional
    :param can_add_special_roles: if the token manager can add special roles, defaults to False
    :type can_add_special_roles: bool, optional
    :param can_transfer_nft_create_role: if the token manager transfer the create role,
        defaults to False
    :type can_transfer_nft_create_role: bool, optional
    :return: the transaction to issue the specified fungible token
    :rtype: Transaction
    """
    config = Config.get_config()
    builder_config = DefaultTransactionBuildersConfiguration(
        chain_id=config.get('CHAIN')
    )

    builder = SemiFungibleTokenIssueBuilder(
        builder_config,
        sender.address,
        token_name,
        token_ticker,
        can_freeze,
        can_wipe,
        can_pause,
        can_mint,
        can_burn,
        can_change_owner,
        can_upgrade,
        can_add_special_roles,
        can_transfer_nft_create_role,
        nonce=sender.nonce
    )

    tx = builder.build()
    tx.signature = sender.signer.sign(tx)

    return tx


def build_meta_issue_tx(
    sender: Account,
    token_name: str,
    token_ticker: str,
    num_decimal: int,
    can_freeze: bool = False,
    can_wipe: bool = False,
    can_pause: bool = False,
    can_mint: bool = False,
    can_burn: bool = False,
    can_change_owner: bool = False,
    can_upgrade: bool = False,
    can_add_special_roles: bool = False,
    can_transfer_nft_create_role: bool = False
) -> Transaction:
    """
    Build a transaction to issue an ESDT fungible token.

    :param sender: account that will send the transaction
    :type sender: Account
    :param token_name: name if the token to issue
    :type token_name: str
    :param token_ticker: tiocker of the token to issue
    :type token_ticker: str
    :param num_decimals: number of decimals of the token
    :type num_decimals: int
    :param can_freeze: if the tokens on specific accounts can be frozen individually,
        defaults to False
    :type can_freeze: bool, optional
    :param can_wipe: if tokens held on frozen accounts can be burnd by the token manager,
        defaults to False
    :type can_wipe: bool, optional
    :param can_pause: if all transactions of the token can be prevented, defaults to False
    :type can_pause: bool, optional
    :param can_mint: if more supply can be minted later on, defaults to False
    :type can_mint: bool, optional
    :param can_burn: if some supply can be burned, defaults to False
    :type can_burn: bool, optional
    :param can_change_owner: if the management of the token can be transfered to another account,
        defaults to False
    :type can_change_owner: bool, optional
    :param can_upgrade: if the properties of the token can be changed by the token manager,
        defaults to False
    :type can_upgrade: bool, optional
    :param can_add_special_roles: if the token manager can add special roles, defaults to False
    :type can_add_special_roles: bool, optional
    :param can_transfer_nft_create_role: if the token manager transfer the create role,
        defaults to False
    :type can_transfer_nft_create_role: bool, optional
    :return: the transaction to issue the specified fungible token
    :rtype: Transaction
    """
    config = Config.get_config()
    builder_config = DefaultTransactionBuildersConfiguration(
        chain_id=config.get('CHAIN')
    )

    builder = MetaFungibleTokenIssueBuilder(
        builder_config,
        sender.address,
        token_name,
        token_ticker,
        num_decimal,
        can_freeze,
        can_wipe,
        can_pause,
        can_mint,
        can_burn,
        can_change_owner,
        can_upgrade,
        can_add_special_roles,
        can_transfer_nft_create_role,
        nonce=sender.nonce
    )

    tx = builder.build()
    tx.signature = sender.signer.sign(tx)

    return tx


def extract_new_token_identifier(on_chain_tx: TransactionOnNetwork) -> str:
    """
    Extract the token id from a successful token issue transaction

    :param on_chain_tx: on chain transaction with results fetched from the gateway of the api
    :type on_chain_tx: TransactionOnNetwork
    :return: token identifier of the new token issued
    :rtype: str
    """
    try:
        token_identifier_topic = on_chain_tx.logs.events[0].topics[0]
    except IndexError as err:
        raise errors.NewTokenIdentifierNotFound from err

    try:
        return token_identifier_topic.raw.decode('utf-8')
    except Exception as err:
        raise errors.ParsingError(token_identifier_topic.hex(), 'token identifier') from err
