"""
author: Etienne Wallet

This module contains some utilities functions for the execution sub package
"""

import time
from mxops.common.providers import MyProxyNetworkProvider
from mxops.smart_values.utils import retrieve_value_from_any


def wait_for_n_blocks(shard: int, n_blocks: int, cooldown: float = 0.2) -> int:
    """
    Wait for a defined number of blocks produced in a shard

    :param shard: shard to monitor for block production
    :type shard: int
    :param n_blocks: number of block productions to wait for
    :type n_blocks: int
    :param cooldown: sleep time between status requests, defaults to 0.2
    :type cooldown: float, optional
    :return: last published block
    :rtype: int
    """
    proxy_provider = MyProxyNetworkProvider()
    shard = retrieve_value_from_any(shard)
    current_block = proxy_provider.get_network_status(shard).block_nonce
    target_block = current_block + n_blocks
    while current_block < target_block:
        time.sleep(cooldown)
        current_block = proxy_provider.get_network_status(shard).block_nonce
    return current_block
