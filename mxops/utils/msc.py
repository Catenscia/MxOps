"""
author: Etienne Wallet

This module contains utils various functions
"""

from configparser import NoOptionError
import hashlib
from pathlib import Path
import re
import time
from typing import List

from multiversx_sdk import Address

from mxops.config.config import Config


def get_tx_link(tx_hash: str) -> str:
    """
    Return the link to a transaction.
    The link will point towards the explorer if it exists, otherwise to the proxy

    :param tx_hash: hash of the transaction
    :type tx_hash: str
    :return: link to the transaction
    :rtype: str
    """
    config = Config.get_config()
    try:
        base_url = config.get("EXPLORER_URL")
    except NoOptionError:
        base_url = config.get("PROXY")
    return f"{base_url}/transactions/{tx_hash}"


def get_account_link(address: str | Address) -> str:
    """
    Return the link to an account.
    The link will point towards the explorer if it exists, otherwise to the proxy

    :param bech32: hash of the transaction
    :type bech32: str
    :return: link to the transaction
    :rtype: str
    """
    config = Config.get_config()
    if isinstance(address, Address):
        bech32 = address.to_bech32()
    else:
        bech32 = address
    try:
        base_url = config.get("EXPLORER_URL")
    except NoOptionError:
        base_url = config.get("PROXY")
    return f"{base_url}/accounts/{bech32}"


def get_file_hash(file_path: Path) -> str:
    """
    Compute the blake2b hash of a file a return it

    :param file_path: path to the file to compute the hash from
    :type file_path: Path
    :return: hash of the file
    :rtype: str
    """
    file_content = file_path.read_bytes()
    return hashlib.blake2b(file_content, digest_size=32).hexdigest()


def int_to_pair_hex(number: int) -> str:
    """
    Transform an integer into its hex representation (without the 0x) and
    ensure that there is an even number of characters by filling with 0 if necessary

    :param number: number to conver
    :type number: int
    :return: hex representation of the number
    :rtype: str
    """
    hex_str = hex(number)[2:]
    if len(hex_str) % 2:
        return "0" + hex_str
    return hex_str


class RateThrottler:
    """
    This class represent a rate throttler
    """

    def __init__(self, number: int, period: float) -> None:
        self.unit_period = period / number
        self.min_next_tick_timestamp = 0

    def tick(self):
        """
        This endpoint is meant to be called before the action to be throttled
        is taken. If it is called faster than the allowed rate, it will wait until
        the correct time.
        """
        current_timestamp = time.time()
        delta = self.min_next_tick_timestamp - current_timestamp
        if delta > 0:
            time.sleep(delta)
        self.min_next_tick_timestamp = time.time() + self.unit_period


def text_contains_all_patterns(text: str, patterns: List[str]) -> bool:
    """
    Check if the given text contains every regex pattern provided in the list

    :param text: text to inspect
    :type text: str
    :param patterns: patterns to find in the text to inspect
    :type patterns: List[str]
    :return: if all the patterns have at least one match
    :rtype: bool
    """
    for pattern in patterns:
        if re.search(pattern, text) is None:
            return False
    return True


def list_contains_at_least_a_match(texts: list[str], pattern: str) -> bool:
    """
    Check if the provided pattern has at least one match in at least one of
    the provided text

    :param texts: texts to inspect
    :type texts: str
    :param pattern: pattern to find in the texts to inspect
    :type pattern: str
    :return: if at least a match is found
    :rtype: bool
    """
    for text in texts:
        if re.search(pattern, text) is not None:
            return True
    return False


def list_contains_every_patterns(texts: list[str], patterns: List[str]) -> bool:
    """
    Check that every pattern has at least one match in at least one of the provided
    text

    :param texts: texts to inspect
    :type texts: list[str]
    :param patterns: patterns to find in the texts to inspect
    :type patterns: List[str]
    :return: if all the patterns have at least one match in every text
    :rtype: bool
    """
    for pattern in patterns:
        if not list_contains_at_least_a_match(texts, pattern):
            return False
    return True
