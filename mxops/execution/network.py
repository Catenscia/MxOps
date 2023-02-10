"""
author: Etienne Wallet

This module contains the functions to pass transactions to the proxy and to monitor them
"""
from typing import List

from multiversx_sdk_cli.transactions import Transaction
from multiversx_sdk_cli.accounts import Address
from multiversx_sdk_network_providers import ProxyNetworkProvider
from multiversx_sdk_network_providers.transactions import TransactionOnNetwork

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


def extract_simple_esdt_transfer(sender: str, receiver: str, data: str) -> OnChainTransfer:
    """
    Extract a simple ESDT transfer from transaction data or smart contract result data

    :param sender: address of the sender of the data in bech32
    :type sender: str
    :param receiver: address of the receiver of the data in bech32
    :type receiver: str
    :param data: data to analyse for simple ESDT transfer
    :type data: str
    :return: Transfer found in the data
    :rtype: OnChainTransfer
    """
    if not data.startswith('ESDTTransfer@'):
        raise ValueError(f'Data does not describe a simple ESDT transfer: {data}')

    try:
        _, token, amount, *_ = data.split('@')
        token = bytearray.fromhex(token).decode()
        amount = str(int(amount, 16))
    except Exception as err:
        raise errors.ParsingError(data, 'ESDTTransfer') from err

    return OnChainTransfer(sender, receiver, token, amount)


def extract_nft_transfer(sender: str, receiver: str, data: str) -> OnChainTransfer:
    """
    Extract a nft transfer from a smart contract result data.

    :param sender: address of the sender of the data in bech32
    :type sender: str
    :param receiver: address of the receiver of the data in bech32
    :type receiver: str
    :param data: data to analyse for nft transfer
    :type data: str
    :return: Transfer found in the data
    :rtype: OnChainTransfer
    """
    if not data.startswith('ESDTNFTTransfer@'):
        raise ValueError(f'Data does not describe a nft transfer: {data}')

    try:
        _, token, nonce, amount, *_ = data.split('@')
        token = bytearray.fromhex(token).decode() + '-' + nonce
        amount = str(int(amount, 16))
    except Exception as err:
        raise errors.ParsingError(data, 'ESDTNFTTransfer') from err

    return OnChainTransfer(sender, receiver, token, amount)


def extract_multi_transfer(sender: str, data: str) -> List[OnChainTransfer]:
    """
    Extract a multi transfer from smart contract result data

    :param sender: address of the sender of the data in bech32
    :type sender: str
    :param data: data to analyse for multi transfer
    :type data: str
    :return: Transfers found in the data
    :rtype: List[OnChainTransfer]
    """
    if not data.startswith('MultiESDTNFTTransfer@'):
        raise ValueError(f'Data does not describe a multi transfer: {data}')

    try:
        _, receiver, n_transfers, *details = data.split('@')
        n_transfers = int(n_transfers, base=16)
        receiver = Address(receiver).bech32()
    except Exception as err:
        raise errors.ParsingError(data, 'MultiESDTNFTTransfer') from err

    transfers = []
    for i in range(n_transfers):
        try:
            token, nonce, amount = details[3*i:3*(i+1)]
            token = bytearray.fromhex(token).decode()
            amount = str(int(amount, 16))
        except Exception as err:
            raise errors.ParsingError(data, 'MultiESDTNFTTransfer') from err
        if nonce != '':
            token += f'-{nonce}'
        transfers.append(OnChainTransfer(sender, receiver, token, amount))

    return transfers


def get_transfers_from_data(sender: str, receiver: str, data: str) -> List[OnChainTransfer]:
    """
    Try to extract token transfers from the data of a transaction or asmart contract result.
    It relies on the transfer format of ESDT.

    :param sender: address of the sender of the data in bech 32
    :type sender: str
    :param receiver: address of the receiver of the data in bech 32
    :type receiver: str
    :param data: data to analyse for transfers
    :type data: str
    :return: tranfers extracted from the data
    :rtype: List[OnChainTransfer]
    """
    try:
        return [extract_simple_esdt_transfer(sender, receiver, data)]
    except ValueError:
        pass

    try:
        return [extract_nft_transfer(sender, receiver, data)]
    except ValueError:
        pass

    try:
        return extract_multi_transfer(sender, data)
    except ValueError:
        pass

    return []


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
    sender = on_chain_tx.sender.bech32()
    receiver = on_chain_tx.receiver.bech32()
    amount = str(on_chain_tx.value)
    if amount != "0":
        transfers.append(OnChainTransfer(
            sender,
            receiver,
            'EGLD',
            amount
        ))
    elif sender != receiver and on_chain_tx.data.startswith('ESDTTransfer'):
        try:
            transfers.append(extract_simple_esdt_transfer(sender, receiver, on_chain_tx.data))
        except errors.ParsingError:
            pass
    elif on_chain_tx.data.startswith('MultiESDTNFTTransfer'):
        try:
            transfers.extend(extract_multi_transfer(sender, on_chain_tx.data))
        except errors.ParsingError:
            pass

    for result in on_chain_tx.contract_results.items:
        sender, receiver = result.sender.bech32(), result.receiver.bech32()
        amount = str(result.value)
        if amount != "0" and not result.is_refund:
            transfers.append(OnChainTransfer(
                sender,
                receiver,
                'EGLD',
                amount
            ))
        else:
            transfers.extend(get_transfers_from_data(sender, receiver, result.data))

    return transfers
