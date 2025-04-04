"""
author: Etienne Wallet

This module contains the functions and classes related to data cache
"""

from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
import json
from typing import Any

from multiversx_sdk import AccountOnNetwork, AccountStorage, Address
from multiversx_sdk.network_providers.proxy_network_provider import (
    account_from_proxy_response,
    account_storage_from_response,
)

from mxops.data import data_path
from mxops.enums import NetworkEnum, LogGroupEnum
from mxops.utils.logger import get_logger

LOGGER = get_logger(LogGroupEnum.DATA)

ACCOUNT_PREFIX = "ACCOUNT"
ACCOUNT_STORAGE_PREFIX = "ACCOUNT_STORAGE"


@dataclass
class CachedData:
    """
    Class reprensenting general cached data
    """

    network: NetworkEnum
    key: str
    data_datetime: datetime  # should always be timezone aware
    data: Any

    def __post_init__(self):
        """
        check the data validity
        """
        if self.data_datetime is None:
            self.data_datetime = datetime.now(tz=timezone.utc)
        if self.data_datetime.tzinfo is None:
            raise ValueError("data datetime must be timezone aware")

    def save(self):
        """
        save this class as cached data
        """
        file_name = f"{self.key}.json"
        file_path = data_path.get_data_cache_file_path(file_name, self.network)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        data = {"data_datetime": self.data_datetime.timestamp(), "data": self.data}
        file_path.write_text(json.dumps(data, indent=4), encoding="utf-8")

    @staticmethod
    def load(key: str, network: NetworkEnum) -> CachedData:
        """
        Load an instance of this class from a save file

        :param key: key identifier of the file
        :type key: str
        :param network: network assigned to the data
        :type network: NetworkEnum
        :return: loaded data
        :rtype: CachedData
        """
        file_name = f"{key}.json"
        file_path = data_path.get_data_cache_file_path(file_name, network)
        raw_content = file_path.read_text(encoding="utf-8")
        content = json.loads(raw_content)
        return CachedData(
            network=network,
            key=key,
            data_datetime=datetime.fromtimestamp(
                content["data_datetime"], tz=timezone.utc
            ),
            data=content["data"],
        )

    @staticmethod
    def try_load_data(
        key: str, network: NetworkEnum, datetime_threshold: datetime | None = None
    ) -> Any | None:
        """
        Try to load existing cached data if it is more recent than the specified
        threshold. Return the inner saved data

        :param key: identifiying key of the data
        :type key: str
        :param network: network of the data
        :type network: NetworkEnum
        :param datetime_threshold: oldest cached data time allowed, defaults to None
        :type datetime_threshold: datetime | None, optional
        :return: inner data saved
        :rtype: Any | None
        """
        try:
            cached_data = CachedData.load(key, network)
        except FileNotFoundError:
            LOGGER.debug(f"No cached data for {key} on {network.value}")
            return None
        if (
            datetime_threshold is None
            or cached_data.data_datetime >= datetime_threshold
        ):
            LOGGER.debug(f"Recent cached data for {key} on {network.value} found")
            return cached_data.data
        LOGGER.debug(f"Cached data for {key} on {network.value} is too old")
        return None


def try_load_account_data(
    network: NetworkEnum, address: Address, datetime_threshold: datetime | None = None
) -> dict | None:
    """
    Load cached data describing an account on the network

    :param network: network of the account
    :type network: NetworkEnum
    :param address: address of the account
    :type address: Address
    :param datetime_threshold: oldest cached data time allowed
    :type datetime_threshold: datetime | None
    :return: cached data
    :rtype: CachedData
    """
    key = f"{ACCOUNT_PREFIX}_{address.to_bech32()}"
    raw_data = CachedData.try_load_data(key, network, datetime_threshold)
    if raw_data is None:
        return None
    return account_from_proxy_response(raw_data)


def save_account_data(
    network: NetworkEnum,
    account: AccountOnNetwork,
    data_datetime: datetime | None = None,
):
    """
    Save data as cache describing an account on the network

    :param network: network of the account
    :type network: NetworkEnum
    :param account: account to save
    :type account: AccountOnNetwork
    :param data_datetime: datetime of the data, default to None wich will be now
    :type data_datetime: dict
    """
    key = f"{ACCOUNT_PREFIX}_{account.address.to_bech32()}"
    CachedData(
        network=network, key=key, data_datetime=data_datetime, data=account.raw
    ).save()


def try_load_account_storage_data(
    network: NetworkEnum, address: Address, datetime_threshold: datetime | None = None
) -> AccountStorage | None:
    """
    Load cached data describing an account's storage on the network

    :param network: network of the account
    :type network: NetworkEnum
    :param address: address of the account
    :type address: Address
    :param datetime_threshold: oldest cached data time allowed
    :type datetime_threshold: datetime | None
    :return: cached data if it exists
    :rtype: AccountStorage | None
    """
    key = f"{ACCOUNT_STORAGE_PREFIX}_{address.to_bech32()}"
    raw_data = CachedData.try_load_data(key, network, datetime_threshold)
    if raw_data is None:
        return None
    return account_storage_from_response(raw_data)


def save_account_storage_data(
    network: NetworkEnum,
    address: Address,
    storage: AccountStorage,
    data_datetime: datetime | None = None,
):
    """
    Save data as cache describing an account's storage on the network

    :param network: network of the account
    :type network: NetworkEnum
    :param address: address of the account
    :type address: Address
    :param storage: data to save
    :type storage: AccountStorage
    :param data_datetime: datetime of the data, default to None wich will be now
    :type data_datetime: dict
    """
    key = f"{ACCOUNT_STORAGE_PREFIX}_{address.to_bech32()}"
    CachedData(
        network=network, key=key, data_datetime=data_datetime, data=storage.raw
    ).save()
