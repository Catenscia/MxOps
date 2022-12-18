"""
author: Etienne Wallet

This module contains the functions to pass transactions to the proxy and to monitor them
"""
from erdpy.proxy import ElrondProxy
from erdpy.transactions import Transaction

from xops.config.config import Config
from xops import errors


def send(tx: Transaction) -> str:
    """
    Send a transaction through the proxy without waiting for a return

    :param tx: transaction to send
    :type tx: Transaction
    :return: hash of the transaction
    :rtype: str
    """
    config = Config.get_config()
    proxy = ElrondProxy(config.get('PROXY'))
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
    proxy = ElrondProxy(config.get('PROXY'))
    timeout = int(config.get('TX_TIMEOUT'))
    return tx.send_wait_result(proxy, timeout)


def check_onchain_success(on_chain_tx: Transaction):
    """
    Raise an error if the transaction failed or if the contract encountered an error

    :param onChainTx: on chain finalised transaction
    :type onChainTx: Transaction
    """
    if not on_chain_tx.is_done():
        raise errors.UnfinalizedTransactionException(on_chain_tx)
    tx_dict = on_chain_tx.to_dictionary()
    if tx_dict['status'] == 'failed':
        raise errors.FailedTransactionError(on_chain_tx)

    try:
        logs = tx_dict['logs']
        events = logs['events']
    except KeyError:
        events = []

    for event in events:
        if event['identifier'] in ['internalVMErrors']:
            raise errors.SmartContractExecutionError(on_chain_tx, logs)
