"""
author: Etienne Wallet

This module contains the function to manage ESDT
"""
from multiversx_sdk_network_providers.transactions import TransactionOnNetwork

from mxops import errors


def extract_new_token_identifier(on_chain_tx: TransactionOnNetwork) -> str:
    """
    Extract the token id from a successful token issue transaction

    :param on_chain_tx: on chain transaction with results fetched from the gateway of
        the api
    :type on_chain_tx: TransactionOnNetwork
    :return: token identifier of the new token issued
    :rtype: str
    """
    try:
        token_identifier_topic = on_chain_tx.logs.events[0].topics[0]
    except IndexError as err:
        raise errors.NewTokenIdentifierNotFound from err

    try:
        return token_identifier_topic.raw.decode("utf-8")
    except Exception as err:
        raise errors.ParsingError(
            token_identifier_topic.hex(), "token identifier"
        ) from err


def extract_new_nonce(on_chain_tx: TransactionOnNetwork) -> int:
    """
    Extract the new created nonce from a successful mint transaction

    :param on_chain_tx: on chain transaction with results fetched from the gateway of
        the api
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
        raise errors.ParsingError(nonce_topic.hex(), "nonce") from err
