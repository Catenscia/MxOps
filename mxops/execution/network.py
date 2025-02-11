"""
author: Etienne Wallet

This module contains the functions to pass transactions to the proxy and to monitor them
"""

import time

from multiversx_sdk import Address, Token, Transaction
from multiversx_sdk import TransactionOnNetwork
from multiversx_sdk.core.constants import EGLD_IDENTIFIER_FOR_MULTI_ESDTNFT_TRANSFER

from mxops.common.providers import MyProxyNetworkProvider
from mxops.config.config import Config
from mxops import errors
from mxops.enums import NetworkEnum
from mxops.execution.msc import OnChainTokenTransfer


def send(tx: Transaction) -> str:
    """
    Send a transaction through the proxy without waiting for a return

    :param tx: transaction to send
    :type tx: Union[CliTransaction, Transaction]
    :return: hash of the transaction
    :rtype: str
    """
    proxy = MyProxyNetworkProvider()
    return proxy.send_transaction(tx).hex()


def send_and_wait_for_result(
    tx: Transaction,
) -> TransactionOnNetwork:
    """
    Transmit a transaction to a proxy constructed with the config.
    Wait for the result of the transaction and return the on-chainfinalised transaction.

    :param tx: transaction to send
    :type tx: Union[CliTransaction, Transaction]
    :return: on chain finalised transaction
    :rtype: TransactionOnNetwork
    """
    config = Config.get_config()
    proxy = MyProxyNetworkProvider()

    timeout = int(config.get("TX_TIMEOUT"))
    refresh_period = float(config.get("TX_REFRESH_PERIOD"))

    tx_hash = proxy.send_transaction(tx).hex()
    num_periods_to_wait = int(timeout / refresh_period)
    if config.get_network() == NetworkEnum.CHAIN_SIMULATOR:
        proxy.generate_blocks_until_tx_completion(tx_hash)

    for _ in range(0, num_periods_to_wait):
        time.sleep(refresh_period)

        on_chain_tx = proxy.get_transaction(tx_hash)
        if on_chain_tx.status.is_completed:
            return on_chain_tx

    raise errors.UnfinalizedTransactionException(on_chain_tx)


def raise_on_errors(on_chain_tx: TransactionOnNetwork):
    """
    Raise an error if the transaction contains any of the following:

    - failed tx
    - smart-contract error
    - internal VM error

    :param onChainTx: on chain finalised transaction
    :type onChainTx: Transaction
    """
    if on_chain_tx.status.status == "invalid":
        raise errors.InvalidTransactionError(on_chain_tx)
    if on_chain_tx.status.status in ("fail", "failed", "unsuccessful"):
        raise errors.FailedTransactionError(on_chain_tx)
    if not on_chain_tx.status.is_completed:
        raise errors.UnfinalizedTransactionException(on_chain_tx)

    event_identifiers = {e.identifier for e in on_chain_tx.logs.events}
    if "InternalVmExecutionError" in event_identifiers:
        raise errors.SmartContractExecutionError(on_chain_tx)
    if "internalVMErrors" in event_identifiers:
        raise errors.InternalVmExecutionError(on_chain_tx)
    if "signalError" in event_identifiers:
        raise errors.TransactionExecutionError(on_chain_tx)


def extract_simple_esdt_transfer(
    sender: Address, receiver: Address, data: str
) -> OnChainTokenTransfer:
    """
    Extract a simple ESDT transfer from transaction data or smart contract result data

    :param sender: address of the sender of the data in bech32
    :type sender: Address
    :param receiver: address of the receiver of the data in bech32
    :type receiver: Address
    :param data: data to analyze for simple ESDT transfer
    :type data: str
    :return: Transfer found in the data
    :rtype: OnChainTokenTransfer
    """
    if not data.startswith("ESDTTransfer@"):
        raise ValueError(f"Data does not describe a simple ESDT transfer: {data}")

    try:
        _, token_identifier, amount, *_ = data.split("@")
        token_identifier = bytearray.fromhex(token_identifier).decode()
        amount = int(amount, 16)
    except Exception as err:
        raise errors.ParsingError(data, "ESDTTransfer") from err

    return OnChainTokenTransfer(sender, receiver, Token(token_identifier), amount)


def extract_nft_transfer(
    sender: Address, receiver: Address, data: str
) -> OnChainTokenTransfer:
    """
    Extract a nft transfer from a smart contract result data.

    :param sender: address of the sender of the data in bech32
    :type sender: Address
    :param receiver: address of the receiver of the data in bech32
    :type receiver: Address
    :param data: data to analyze for nft transfer
    :type data: str
    :return: Transfer found in the data
    :rtype: OnChainTokenTransfer
    """
    if not data.startswith("ESDTNFTTransfer@"):
        raise ValueError(f"Data does not describe a nft transfer: {data}")

    try:
        _, token_identifier, nonce, amount, *_ = data.split("@")
        token_identifier = bytearray.fromhex(token_identifier).decode()
        nonce = int(nonce, base=16)
        amount = int(amount, 16)
    except Exception as err:
        raise errors.ParsingError(data, "ESDTNFTTransfer") from err

    return OnChainTokenTransfer(
        sender, receiver, Token(token_identifier, nonce), amount
    )


def extract_multi_transfer(sender: Address, data: str) -> list[OnChainTokenTransfer]:
    """
    Extract a multi transfer from smart contract result data

    :param sender: address of the sender of the data in bech32
    :type sender: Address
    :param data: data to analyze for multi transfer
    :type data: str
    :return: Transfers found in the data
    :rtype: list[OnChainTokenTransfer]
    """
    if not data.startswith("MultiESDTNFTTransfer@"):
        raise ValueError(f"Data does not describe a multi transfer: {data}")

    try:
        _, receiver, n_transfers, *details = data.split("@")
        n_transfers = int(n_transfers, base=16)
        receiver = Address.from_hex(receiver, hrp="erd")
    except Exception as err:
        raise errors.ParsingError(data, "MultiESDTNFTTransfer") from err

    transfers = []
    for i in range(n_transfers):
        try:
            token_identifier, nonce, amount = details[3 * i : 3 * (i + 1)]
            token_identifier = bytearray.fromhex(token_identifier).decode()
            amount = int(amount, 16)
        except Exception as err:
            raise errors.ParsingError(data, "MultiESDTNFTTransfer") from err
        if nonce != "":
            nonce = int(nonce, base=16)
        else:
            nonce = 0
        if token_identifier == EGLD_IDENTIFIER_FOR_MULTI_ESDTNFT_TRANSFER:
            token_identifier = "EGLD"  # nosec
        transfers.append(
            OnChainTokenTransfer(
                sender, receiver, Token(token_identifier, nonce), amount
            )
        )

    return transfers


def get_transfers_from_data(
    sender: str, receiver: str, data: str
) -> list[OnChainTokenTransfer]:
    """
    Try to extract token transfers from the data of a transaction or
    a smart contract result.
    It relies on the transfer format of ESDT.

    :param sender: address of the sender of the data in bech 32
    :type sender: str
    :param receiver: address of the receiver of the data in bech 32
    :type receiver: str
    :param data: data to analyze for transfers
    :type data: str
    :return: tranfers extracted from the data
    :rtype: list[OnChainTokenTransfer]
    """
    try:
        return [extract_simple_esdt_transfer(sender, receiver, data)]
    except (ValueError, errors.ParsingError):
        pass

    try:
        return [extract_nft_transfer(sender, receiver, data)]
    except (ValueError, errors.ParsingError):
        pass

    try:
        return extract_multi_transfer(sender, data)
    except (ValueError, errors.ParsingError):
        pass

    return []


def get_on_chain_transfers(
    on_chain_tx: TransactionOnNetwork, include_refund: bool = False
) -> list[OnChainTokenTransfer]:
    """
    Extract from an on-chain transaction the tokens transfers that were operated in this
    transaction.

    :param on_chain_tx: on-chain transaction to inspect
    :type on_chain_tx: TransactionOnNetwork
    :param include_refund: if gas refund should be included in the transfers returned
    :type include_refund: bool, default to False
    :return: list of executed transfer
    :rtype: list[OnChainTokenTransfers]
    """
    transfers = []
    sender = on_chain_tx.sender
    receiver = on_chain_tx.receiver
    amount = int(on_chain_tx.value)
    data = on_chain_tx.data.decode()
    if amount != 0:
        transfers.append(OnChainTokenTransfer(sender, receiver, Token("EGLD"), amount))
    elif sender != receiver and data.startswith("ESDTTransfer"):
        try:
            transfers.append(extract_simple_esdt_transfer(sender, receiver, data))
        except errors.ParsingError:
            pass
    elif data.startswith("MultiESDTNFTTransfer"):
        try:
            transfers.extend(extract_multi_transfer(sender, data))
        except errors.ParsingError:
            pass

    for result in on_chain_tx.smart_contract_results:
        r_sender, r_receiver = result.sender, result.receiver
        amount = int(result.raw["value"])
        if amount != 0 and (include_refund or not result.raw.get("isRefund", False)):
            transfers.append(
                OnChainTokenTransfer(r_sender, r_receiver, Token("EGLD"), amount)
            )
        elif "data" in result.raw:
            transfers.extend(
                get_transfers_from_data(r_sender, r_receiver, result.raw["data"])
            )

    return transfers
