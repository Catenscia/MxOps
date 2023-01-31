"""
author: Etienne Wallet

This module contains the functions to pass transactions to the proxy and to monitor them
"""
from typing import List

from multiversx_sdk_cli.transactions import Transaction
from multiversx_sdk_cli.accounts import Address
from multiversx_sdk_network_providers import ProxyNetworkProvider
from multiversx_sdk_network_providers.transactions import TransactionOnNetwork, TransactionLogs
from multiversx_sdk_network_providers.transaction_events import TransactionEvent

from mxops.config.config import Config
from mxops import errors
from mxops.execution.msc import OnChainTransfer


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
    if 'InternalVmExecutionError' in event_identifiers:
        raise errors.SmartContractExecutionError(on_chain_tx)
    if 'internalVMErrors' in event_identifiers:
        raise errors.InternalVmExecutionError(on_chain_tx)
    if 'signalError' in event_identifiers:
        raise errors.TransactionExecutionError(on_chain_tx)


def get_transfer_from_event(event: TransactionEvent):
    """_summary_

    :param event: _description_
    :type event: TransactionEvent
    """
    if 'Transfer' not in event.identifier:
        return None
    token, nonce, amount, receiver = [t.raw for t in event.topics]
    token = token.decode()
    nonce = nonce.hex()
    if nonce != '':
        token += '-' + nonce
    receiver = Address(receiver.hex()).bech32()
    amount = str(int(amount.hex(), 16))
    return OnChainTransfer(event.address.bech32(), receiver, token, amount)


def get_transfers_from_logs(on_chain_logs: TransactionLogs) -> List[OnChainTransfer]:
    """_summary_

    :param on_chain_logs: _description_
    :type on_chain_logs: TransactionLogs
    :return: _description_
    :rtype: List[OnChainTransfer]
    """
    transfers = []
    for event in on_chain_logs.events:
        transfer = get_transfer_from_event(event)
        if transfer is not None:
            transfers.append(transfer)
    return transfers


def get_on_chain_transfers(on_chain_tx: TransactionOnNetwork) -> List[OnChainTransfer]:
    """
    Extract from an on-chain transaction the tokens transfers that were operated in this
    transaction.

    :param on_chain_tx: on-chain transaction to inspect
    :type on_chain_tx: TransactionOnNetwork
    :return: list of executed transfer
    :rtype: List[OnChainTransfer]
    """
    transfers = []
    if on_chain_tx.value != "0":
        transfers.append(OnChainTransfer(
            on_chain_tx.sender.bech32(),
            on_chain_tx.receiver.bech32(),
            'EGLD',
            on_chain_tx.value
        ))

    for result in on_chain_tx.contract_results.items:
        sender, receiver = result.sender.bech32(), result.receiver.bech32()
        if result.value != 0 and sender != receiver:
            transfers.append(OnChainTransfer(
                result.sender,
                result.receiver,
                'EGLD',
                result.value
            ))
        transfers.extend(get_transfers_from_logs(result.logs))

    transfers.extend(get_transfers_from_logs(on_chain_tx.logs))
    return transfers
