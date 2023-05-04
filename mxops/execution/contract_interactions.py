"""
Module with deploy, call and queries functions for the contracts
"""
from pathlib import Path
from typing import List, Tuple

from multiversx_sdk_cli import config as mxpy_config
from multiversx_sdk_cli.accounts import Account
from multiversx_sdk_cli.contracts import CodeMetadata, SmartContract, QueryResult
from multiversx_sdk_cli.transactions import Transaction as CliTransaction
from multiversx_sdk_cli import utils as mxpy_utils
from multiversx_sdk_network_providers import ProxyNetworkProvider

from mxops.config.config import Config
from mxops.execution.msc import EsdtTransfer
from mxops.execution import utils


def get_contract_deploy_tx(
    wasm_file: Path,
    metadata: CodeMetadata,
    gas_limit: int,
    contract_args: List,
    sender: Account
) -> Tuple[CliTransaction, SmartContract]:
    """
    Contruct the contract instance and the transaction used to deploy a contract.
    The transaction is not relayed to the proxy,
    this has to be done with the result of this function.

    :param wasm_file: path to the wasm file of the contract
    :type wasm_file: Path
    :param metadata: metadata for the contract deployment
    :type metadata: CodeMetadata
    :param gas_limit: gas limit for the transaction
    :type gas_limit: int
    :param contract_args: list of arguments to pass to the deploy method
    :type contract_args: List
    :param sender: account to use for this transaction
    :type sender: Account
    :return: deploy transaction and contract instance created
    :rtype: Tuple[CliTransaction, SmartContract]
    """
    config = Config.get_config()

    bytecode = mxpy_utils.read_binary_file(wasm_file).hex()
    contract = SmartContract(bytecode=bytecode, metadata=metadata)
    formated_args = utils.format_tx_arguments(contract_args)

    tx = contract.deploy(sender, formated_args, mxpy_config.DEFAULT_GAS_PRICE,
                         gas_limit, 0, config.get('CHAIN'), mxpy_config.get_tx_version())

    return tx, contract


def get_contract_value_call_tx(
    contract_str: str,
    endpoint: str,
    gas_limit: int,
    arguments: List,
    value: int,
    sender: Account
) -> CliTransaction:
    """
    Contruct the transaction for a contract call with value provision.
    The transaction is not relayed to the proxy, this has to be done with
    the result of this function.

    :param contract_str: designation of the contract to call (bech32 or mxops value)
    :type contract_str: str
    :param endpoint: endpoint to call
    :type endpoint: str
    :param gas_limit: gas limit for the transaction.
    :type gas_limit:int
    :param arguments: argument for endpoint
    :type arguments: List
    :param value: value to send during the call
    :type value: int
    :param sender: sender of the transaction
    :type sender: Account
    :return: call transaction to send
    :rtype: CliTransaction
    """
    config = Config.get_config()

    contract = utils.get_contract_instance(contract_str)

    formated_args = utils.format_tx_arguments(arguments)
    if isinstance(value, str):
        value = utils.retrieve_value_from_string(value)

    tx = contract.execute(
        caller=sender,
        function=endpoint,
        arguments=formated_args,
        value=value,
        gas_price=mxpy_config.DEFAULT_GAS_PRICE,
        gas_limit=gas_limit,
        chain=config.get('CHAIN'),
        version=mxpy_config.get_tx_version()
    )

    return tx


def get_contract_single_esdt_call_tx(
    contract_str: str,
    endpoint: str,
    gas_limit: int,
    arguments: List,
    esdt_transfer: EsdtTransfer,
    sender: Account
) -> CliTransaction:
    """
    Contruct the transaction for a contract call with an esdt transfer.
    The transaction is not relayed to the proxy, this has to be done with
    the result of this function.

    :param contract_str: designation of the contract to call (bech32 or mxops value)
    :type contract_str: str
    :param endpoint: endpoint to call
    :type endpoint: str
    :param gas_limit: gas limit for the transaction.
    :type gas_limit:int
    :param arguments: argument for endpoint
    :type arguments: List
    :param esdt_transfer: transfer to be made with the endpoint call
    :type esdt_transfer: EsdtTransfer
    :param sender: sender of the transaction
    :type sender: Account
    :return: call transaction to send
    :rtype: CliTransaction
    """
    config = Config.get_config()

    contract = utils.get_contract_instance(contract_str)

    tx_arguments = [
        esdt_transfer.token_identifier,
        esdt_transfer.amount,
        endpoint,
        *arguments
    ]
    formated_args = utils.format_tx_arguments(tx_arguments)

    tx = contract.execute(
        caller=sender,
        function='ESDTTransfer',
        arguments=formated_args,
        value=0,
        gas_price=mxpy_config.DEFAULT_GAS_PRICE,
        gas_limit=gas_limit,
        chain=config.get('CHAIN'),
        version=mxpy_config.get_tx_version()
    )

    return tx


def get_contract_single_nft_call_tx(
    contract_str: str,
    endpoint: str,
    gas_limit: int,
    arguments: List,
    nft_transfer: EsdtTransfer,
    sender: Account
) -> CliTransaction:
    """
    Contruct the transaction for a contract call with an nft transfer (NFT, SFT and Meta ESDT).
    The transaction is not relayed to the proxy, this has to be done with
    the result of this function.

    :param contract_str: designation of the contract to call (bech32 or mxops value)
    :type contract_str: str
    :param endpoint: endpoint to call
    :type endpoint: str
    :param gas_limit: gas limit for the transaction.
    :type gas_limit:int
    :param arguments: argument for endpoint
    :type arguments: List
    :param nft_transfer: transfer to be made with the endpoint call
    :type nft_transfer: EsdtTransfer
    :param sender: sender of the transaction
    :type sender: Account
    :return: call transaction to send
    :rtype: CliTransaction
    """
    config = Config.get_config()
    self_contract = SmartContract(sender.address)

    contract = utils.get_contract_instance(contract_str)

    tx_arguments = [
        nft_transfer.token_identifier,
        nft_transfer.nonce,
        nft_transfer.amount,
        contract.address.bech32(),
        endpoint,
        *arguments
    ]
    formated_args = utils.format_tx_arguments(tx_arguments)

    tx = self_contract.execute(
        caller=sender,
        function='ESDTNFTTransfer',
        arguments=formated_args,
        value=0,
        gas_price=mxpy_config.DEFAULT_GAS_PRICE,
        gas_limit=gas_limit,
        chain=config.get('CHAIN'),
        version=mxpy_config.get_tx_version()
    )

    return tx


def get_contract_multiple_esdt_call_tx(
    contract_str: str,
    endpoint: str,
    gas_limit: int,
    arguments: List,
    esdt_transfers: List[EsdtTransfer],
    sender: Account
) -> CliTransaction:
    """
    Contruct the transaction for a contract call with multiple esdt transfers.
    The transaction is not relayed to the proxy, this has to be done with
    the result of this function.

    :param contract_str: designation of the contract to call (bech32 or mxops value)
    :type contract_str: str
    :param endpoint: endpoint to call
    :type endpoint: str
    :param gas_limit: gas limit for the transaction.
    :type gas_limit:int
    :param arguments: argument for endpoint
    :type arguments: List
    :param esdt_transfers: transfers to be made with the endpoint call
    :type esdt_transfers: List[EsdtTransfer]
    :param sender: sender of the transaction
    :type sender: Account
    :return: call transaction to send
    :rtype: CliTransaction
    """
    config = Config.get_config()

    self_contract = SmartContract(sender.address)
    contract = utils.get_contract_instance(contract_str)

    tx_arguments = [
        contract.address.bech32(),
        len(esdt_transfers)
    ]
    for esdt_transfer in esdt_transfers:
        tx_arguments.extend([
            esdt_transfer.token_identifier,
            esdt_transfer.nonce,
            esdt_transfer.amount,
        ])

    tx_arguments.extend([endpoint, *arguments])
    formated_args = utils.format_tx_arguments(tx_arguments)

    tx = self_contract.execute(
        caller=sender,
        function='MultiESDTNFTTransfer',
        arguments=formated_args,
        value=0,
        gas_price=mxpy_config.DEFAULT_GAS_PRICE,
        gas_limit=gas_limit,
        chain=config.get('CHAIN'),
        version=mxpy_config.get_tx_version()
    )

    return tx


def get_contract_call_tx(
    contract_str: str,
    endpoint: str,
    gas_limit: int,
    arguments: List,
    value: int,
    esdt_transfers: List[EsdtTransfer],
    sender: Account
) -> CliTransaction:
    """
    Contruct the transaction for a contract call
    The transaction is not relayed to the proxy, this has to be done with
    the result of this function.

    :param contract_str: designation of the contract to call (bech32 or mxops value)
    :type contract_str: str
    :param endpoint: endpoint to call
    :type endpoint: str
    :param gas_limit: gas limit for the transaction.
    :type gas_limit:int
    :param arguments: argument for endpoint
    :type arguments: List
    :param value: value to send during the call
    :type value: int
    :param esdt_transfers: transfers to be made with the endpoint call
    :type esdt_transfers: List[EsdtTransfer]
    :param sender: sender of the transaction
    :type sender: Account
    :return: call transaction to send
    :rtype: CliTransaction
    """
    n_transfers = len(esdt_transfers)

    if n_transfers == 0:
        tx = get_contract_value_call_tx(contract_str,
                                        endpoint,
                                        gas_limit,
                                        arguments,
                                        value,
                                        sender)
    elif n_transfers == 1:
        transfer = esdt_transfers[0]
        if transfer.nonce:
            tx = get_contract_single_nft_call_tx(contract_str,
                                                 endpoint,
                                                 gas_limit,
                                                 arguments,
                                                 transfer,
                                                 sender)
        else:
            tx = get_contract_single_esdt_call_tx(contract_str,
                                                  endpoint,
                                                  gas_limit,
                                                  arguments,
                                                  transfer,
                                                  sender)
    else:
        tx = get_contract_multiple_esdt_call_tx(contract_str,
                                                endpoint,
                                                gas_limit,
                                                arguments,
                                                esdt_transfers,
                                                sender)

    return tx


def query_contract(contract_str: str, endpoint: str, arguments: List) -> List[QueryResult]:
    """
    Query a contract to retireve some values.

    :param contract_str: designation of the contract to call (bech32 or mxops value)
    :type contract_str: str
    :param endpoint: endpoint to query
    :type endpoint: str
    :param arguments: argument for endpoint
    :type arguments: List
    :return: list of QueryResult
    :rtype: List[QueryResult]
    """
    config = Config.get_config()
    proxy = ProxyNetworkProvider(config.get('PROXY'))

    contract = utils.get_contract_instance(contract_str)
    formated_args = utils.format_tx_arguments(arguments)

    results = contract.query(
        proxy=proxy,
        function=endpoint,
        arguments=formated_args,
    )
    return results
