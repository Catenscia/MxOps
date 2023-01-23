"""
author: Etienne Wallet

This module contains the functions to pass transactions to the proxy and to monitor them
"""
from multiversx_sdk_network_providers import ProxyNetworkProvider
from multiversx_sdk_cli.transactions import Transaction
from multiversx_sdk_network_providers.transactions import TransactionOnNetwork
from multiversx_sdk_network_providers.transaction_status import TransactionStatus

from mxops.config.config import Config
from mxops import errors


def send(tx: Transaction) -> str:
    """
    Send a transaction through the proxy without waiting for a return

    :param tx: transaction to send
    :type tx: Transaction
    :return: hash of the transaction
    :rtype: str
    """
    config = Config.get_config()
    proxy = ProxyNetworkProvider(config.get('PROXY'))
    return tx.send(proxy)


def send_and_wait_for_result(tx: Transaction) -> Transaction:
    """
    Transmit a transaction to a proxy constructed with the config.
    Wait for the result of the transaction and return the on-chainfinalised transaction.

    :param tx: transaction to send
    :type tx: Transaction
    :return: on chain finalised transaction
    :rtype: Transaction
    """
    config = Config.get_config()
    proxy = ProxyNetworkProvider(config.get('PROXY'))
    timeout = int(config.get('TX_TIMEOUT'))
    return tx.send_wait_result(proxy, timeout)


def raise_on_errors(on_chain_tx: TransactionOnNetwork):
    """
    Raise an error if the transaction contains any of the following:

    - failed tx
    - smart-contract error
    - internal VM error

    :param onChainTx: on chain finalised transaction
    :type onChainTx: Transaction
    """
    if not on_chain_tx.is_completed:
        raise errors.UnfinalizedTransactionException(on_chain_tx)

    if on_chain_tx.status.is_invalid():
        raise errors.InvalidTransactionError(on_chain_tx)
    if on_chain_tx.status.is_failed():
        raise errors.FailedTransactionError(on_chain_tx)

    event_identifiers = {e.identifier for e in on_chain_tx.logs.events}
    if  'InternalVmExecutionError' in event_identifiers:
        raise errors.SmartContractExecutionError(on_chain_tx)
    if 'internalVMErrors' in event_identifiers:
        raise errors.InternalVmExecutionError(on_chain_tx)
    if 'signalError' in event_identifiers:
        raise errors.TransactionExecutionError(on_chain_tx)
