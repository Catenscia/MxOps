"""
author: Etienne Wallet

This module contains utils various functions
"""
import hashlib
from pathlib import Path

from xops.config.config import Config


def get_proxy_tx_link(tx_hash: str) -> str:
    """
    Return the link to a transaction using the proxy in the config

    :param tx_hash: hash of the transaction
    :type tx_hash: str
    :return: link to the transaction
    :rtype: str
    """
    config = Config.get()
    proxy = config.get('PROXY')
    return f'{proxy}/transaction/{tx_hash}'



def get_file_hash(file_path: Path) -> str:
    """
    Compute the sha256 hash of a file a return it

    :param file_path: path to the file to compute the hash from
    :type file_path: Path
    :return: hash of the file
    :rtype: str
    """
    block_size = 65536
    file_hash = hashlib.sha256()
    with open(file_path.as_posix(), 'rb') as f:
        fb = f.read(block_size)
        while len(fb) > 0:
            file_hash.update(fb)
            fb = f.read(block_size)
    return file_hash.hexdigest()
