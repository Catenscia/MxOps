"""
author: Etienne Wallet

This module contains utils various functions related to wallets
"""

from typing import Optional, Tuple

from multiversx_sdk import Address
from multiversx_sdk.wallet import Mnemonic, UserPEM

from mxops import errors


def get_shard_of_pubkey(pubkey: bytes) -> int:
    """
    Compute the shard asssigned to a wallet from a public key

    :param pubkey: public key of a wallet
    :type pubkey: bytes
    :return: shard of the wallet
    :rtype: int
    """
    mask_high = int("11", 2)
    last_byte_of_pubkey = pubkey[31]
    shard = last_byte_of_pubkey & mask_high

    return shard


def generate_pem_wallet(shard: Optional[int] = None) -> Tuple[UserPEM, Address]:
    """
    Generate a MultiversX PEM wallet

    :param shard: wanted shard of the wallets, random if not specified, defaults to None
    :type shard: Optional[int], optional
    :return: generated wallet and its address
    :rtype: Tuple[UserPEM, Address]
    """
    k_iter = 0
    while k_iter < 10000:
        mnemonic = Mnemonic.generate()
        secret_key = mnemonic.derive_key(0)
        public_key = secret_key.generate_public_key()
        address = Address(public_key.buffer, "erd")
        address_shard = get_shard_of_pubkey(address.pubkey)
        if shard is None or address_shard == shard:
            return UserPEM(label=address.bech32(), secret_key=secret_key), address
        k_iter += 1

    raise errors.MaxIterations("Failed to find a fitting wallet within max iterations")
