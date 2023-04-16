"""
Module with functions to create transfers transactions
"""
from typing import Union

from multiversx_sdk_core import TokenPayment, Transaction
from multiversx_sdk_core import transaction_builders as tx_builder
from multiversx_sdk_cli.accounts import Account

from mxops.config.config import Config
from mxops.execution import utils


def get_egld_transfer_tx(
        sender: Account,
        reciever_str: str,
        amount: Union[int, str]
) -> Transaction:
    """
    Contruct a transaction with a eGLD transfer from the provided arguments. All inputs will
    be dynamically evaluated if needed

    :param sender: Account that sends the transaction
    :type sender: Account
    :param reciever_str: raw address or smart values that designates the recieving address
    :type reciever_str: str
    :param amount: amount of eGLD to send (or smart values)
    :type amount: Union[int, str]
    :return: transaction containing the transfers described
    :rtype: Transaction
    """
    config = Config.get_config()
    builder_config = tx_builder.DefaultTransactionBuildersConfiguration(
        chain_id=config.get('CHAIN')
        )

    receiver_address = utils.get_address_instance(reciever_str)
    if isinstance(amount, str):
        amount = int(utils.retrieve_value_from_string(amount))
    payment = TokenPayment.egld_from_integer(amount)

    builder = tx_builder.EGLDTransferBuilder(
        config=builder_config,
        sender=sender.address,
        receiver=receiver_address,
        payment=payment,
        nonce=sender.nonce
    )

    tx = builder.build()
    tx.signature = sender.sign_transaction(tx)

    return tx


def get_esdt_transfer_tx(
        sender: Account,
        reciever_str: str,
        token_identifier: str,
        amount: Union[int, str],
) -> Transaction:
    """
    Contruct a transaction with a ESDT transfer from the provided arguments. All inputs will
    be dynamically evaluated if needed

    :param sender: Account that sends the transaction
    :type sender: Account
    :param reciever_str: raw address or smart values that designates the recieving address
    :type reciever_str: str
    :param token_identifier: raw token identifier or smart value
    :type token_identifier: str
    :param amount: amount of ESDT to send (or smart values)
    :type amount: Union[int, str]
    :return: transaction containing the transfers described
    :rtype: Transaction
    """
    config = Config.get_config()
    builder_config = tx_builder.DefaultTransactionBuildersConfiguration(
        chain_id=config.get('CHAIN')
        )

    receiver_address = utils.get_address_instance(reciever_str)
    token_identifier = utils.retrieve_value_from_string(token_identifier)
    if isinstance(amount, str):
        amount = int(utils.retrieve_value_from_string(amount))
    payment = TokenPayment.fungible_from_integer(token_identifier, amount, 0)

    builder = tx_builder.ESDTTransferBuilder(
        config=builder_config,
        sender=sender.address,
        receiver=receiver_address,
        payment=payment,
        nonce=sender.nonce
    )

    tx = builder.build()
    tx.signature = sender.sign_transaction(tx)

    return tx


def get_esdt_nft_transfer_tx(
        sender: Account,
        reciever_str: str,
        token_identifier: str,
        nonce: Union[int, str],
        amount: Union[int, str],
) -> Transaction:
    """
    Contruct a transaction with a ESDT NFT (NFT, SFT or Meta ESDT) transfer from the provided
    arguments. All inputs will be dynamically evaluated if needed

    :param sender: Account that sends the transaction
    :type sender: Account
    :param reciever_str: raw address or smart values that designates the recieving address
    :type reciever_str: str
    :param token_identifier: raw token identifier or smart value
    :type token_identifier: str
    :param nonce: nonce of the token to send (or smart values)
    :type nonce: Union[int, str]
    :param amount: amount of ESDT NFT to send (or smart values)
    :type amount: Union[int, str]
    :return: transaction containing the transfers described
    :rtype: Transaction
    """
    config = Config.get_config()
    builder_config = tx_builder.DefaultTransactionBuildersConfiguration(
        chain_id=config.get('CHAIN')
        )

    receiver_address = utils.get_address_instance(reciever_str)
    token_identifier = utils.retrieve_value_from_string(token_identifier)
    if isinstance(nonce, str):
        nonce = int(utils.retrieve_value_from_string(nonce))
    if isinstance(amount, str):
        amount = int(utils.retrieve_value_from_string(amount))
    payment = TokenPayment.meta_esdt_from_integer(token_identifier, amount, nonce, 0)

    builder = tx_builder.ESDTNFTTransferBuilder(
        config=builder_config,
        sender=sender.address,
        receiver=receiver_address,
        payment=payment,
        nonce=sender.nonce
    )

    tx = builder.build()
    tx.signature = sender.sign_transaction(tx)

    return tx


# TODO add get_mutli_esdt_nft_transfer from MultiESDTNFTTransferBuilder