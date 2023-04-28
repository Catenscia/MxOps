"""
author: Etienne Wallet

This module contains the function to manage ESDT
"""
from multiversx_sdk_cli.accounts import Account
from multiversx_sdk_core import Transaction
from multiversx_sdk_network_providers.transactions import TransactionOnNetwork

from mxops.config.config import Config
from mxops import errors
from mxops.execution import token_management_builders


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
    builder_config = token_management_builders.MyDefaultTransactionBuildersConfiguration(
        chain_id=config.get('CHAIN')
    )

    builder = token_management_builders.FungibleTokenIssueBuilder(
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
    builder_config = token_management_builders.MyDefaultTransactionBuildersConfiguration(
        chain_id=config.get('CHAIN')
    )

    builder = token_management_builders.NonFungibleTokenIssueBuilder(
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
    builder_config = token_management_builders.MyDefaultTransactionBuildersConfiguration(
        chain_id=config.get('CHAIN')
    )

    builder = token_management_builders.SemiFungibleTokenIssueBuilder(
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
    builder_config = token_management_builders.MyDefaultTransactionBuildersConfiguration(
        chain_id=config.get('CHAIN')
    )

    builder = token_management_builders.MetaFungibleTokenIssueBuilder(
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


def extract_new_nonce(on_chain_tx: TransactionOnNetwork) -> int:
    """
    Extract the new created nonce from a successful mint transaction

    :param on_chain_tx: on chain transaction with results fetched from the gateway of the api
    :type on_chain_tx: TransactionOnNetwork
    :return: created nonce
    :rtype: int
    """
    try:
        nonce_topic = on_chain_tx.logs.events[0].topics[1]
    except IndexError as err:
        raise errors.NewTokenIdentifierNotFound from err

    try:
        return int(nonce_topic.hex(), 16)
    except Exception as err:
        raise errors.ParsingError(nonce_topic.hex(), 'nonce') from err
