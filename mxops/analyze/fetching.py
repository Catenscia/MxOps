"""
author: Etienne Wallet

This module handles the data fetching from the network
"""
from datetime import datetime, timezone
from tqdm import tqdm

from multiversx_sdk_network_providers import GenericError, ApiNetworkProvider

from mxops.config.config import Config
from mxops.data.analyze_data import TransactionsData
from mxops.utils.logger import get_logger
from mxops.utils.msc import RateThrottler

LOGGER = get_logger("fetching")


def update_transactions_data(txs_data: TransactionsData):
    """
    Update the transactions data for a contract.
    The data is not saved on the drive in this function

    :param txs_data: data to update
    :type txs_data: TransactionsData
    """
    config = Config.get_config()
    LOGGER.info(
        f"Updating transactions for {txs_data.contract_beh32_address} "
        f"on {config.get_network().value}"
    )
    pbar = tqdm(desc="Fetching data")
    throttler = RateThrottler(int(config.get("API_RATE_LIMIT")), 1)
    api_provider = ApiNetworkProvider(config.get("API"))
    while True:
        resource_url = (
            f"accounts/{txs_data.contract_beh32_address}/transactions?"
            f"size=50&from={txs_data.transactions_offset}&after="
            f"{txs_data.transactions_offset_origin}&order=asc&"
            "withScResults=true"
        )
        error_count = 0
        raw_txs = None
        while raw_txs is None:
            try:
                throttler.tick()
                raw_txs = api_provider.do_get_generic_collection(resource_url)
            except GenericError as err:
                error_count += 1
                if error_count >= 3:
                    raise err

        if len(raw_txs) == 0:
            pbar.set_description("all transactions have been fetched")
            pbar.close()
            txs_data.save()
            return

        txs_data.add_transactions(raw_txs)

        most_recent_tx = sorted(raw_txs, key=lambda x: x["timestamp"], reverse=True)[0]
        most_recent_timestamp = most_recent_tx["timestamp"]
        datetime_str = datetime.fromtimestamp(
            most_recent_timestamp, tz=timezone.utc
        ).isoformat()
        pbar.set_description("Transaction fetched up until " f"{datetime_str}")
        pbar.update(len(raw_txs))
        txs_data.transactions_offset += len(raw_txs)

        if txs_data.transactions_offset > 2500:
            txs_data.transactions_offset = 0
            txs_data.transactions_offset_origin = most_recent_timestamp - 1
            txs_data.save()
