"""
author: Etienne Wallet

This module format transactions data in a usable manner for the plots
"""
from datetime import datetime, timezone
from typing import Dict

import pandas as pd

from mxops.data.analyze_data import TransactionsData
from mxops.utils.logger import get_logger


LOGGER = get_logger("agglomerate")


def extrat_df_raw_row(raw_tx: Dict) -> Dict:
    """
    From a raw transaction, select and transfrom the data that will be
    included in the transaction dataframe

    :param raw_tx: raw tranasction as received from the api
    :type raw_tx: Dict
    :return: extracted data
    :rtype: Dict
    """
    # For now only basic selection but complexe extraction will be done here
    # in future version
    tx_data = {
        "txHash": raw_tx["txHash"],
        "gasLimit": raw_tx["gasLimit"],
        "gasUsed": raw_tx["gasUsed"],
        "sender": raw_tx["sender"],
        "status": raw_tx["status"],
        "fee": int(raw_tx["fee"]),
        "datetime": datetime.fromtimestamp(raw_tx["timestamp"], tz=timezone.utc),
        "function": raw_tx["function"],
    }
    return tx_data


def get_transactions_df(transactions_data: TransactionsData) -> pd.DataFrame:
    """
    Create a dataframe from the transactions data

    :param transactions_data: transactions data for a contract
    :type transactions_data: TransactionsData
    :return: dataframe of the transaction
    :rtype: pd.DataFrame
    """
    txs_data = []
    for raw_tx in transactions_data.raw_transactions.values():
        try:
            txs_data.append(extrat_df_raw_row(raw_tx))
        except Exception as err:
            LOGGER.warning(f"A raw transaction could not be processed: {raw_tx}: {err}")
    df = pd.DataFrame(txs_data)
    df["date"] = df["datetime"].dt.date
    return df


def get_status_per_day_df(txs_df: pd.DataFrame) -> pd.DataFrame:
    """
    Transform the transactions dataframe to aggregate the transactions
    status per day

    :param txs_df: dataframe with all the transactions
    :type txs_df: pd.DataFrame
    :return: transactions status aggregated per day
    :rtype: pd.DataFrame
    """
    # Counting each status type per day
    status_per_day_df = txs_df.pivot_table(
        index="date", columns="status", aggfunc="size", fill_value=0
    )

    for expected_col in ["success", "fail"]:
        if expected_col not in status_per_day_df.columns:
            status_per_day_df[expected_col] = 0

    # sorting columns
    status_per_day_df = status_per_day_df[sorted(status_per_day_df.columns)]

    # Adding total column
    status_per_day_df["total"] = status_per_day_df.sum(axis=1)
    return status_per_day_df


def get_function_per_day_df(txs_df: pd.DataFrame) -> pd.DataFrame:
    """
    Transform the transactions dataframe to aggregate the transactions
    function per day

    :param txs_df: dataframe with all the transactions
    :type txs_df: pd.DataFrame
    :return: transactions function aggregated per day
    :rtype: pd.DataFrame
    """
    # Counting each status type per day
    function_per_day_df = txs_df.pivot_table(
        index="date", columns="function", aggfunc="size", fill_value=0
    )

    # sorting columns
    function_per_day_df = function_per_day_df[sorted(function_per_day_df.columns)]

    # Adding total column
    function_per_day_df["total"] = function_per_day_df.sum(axis=1)
    return function_per_day_df


def get_unique_users_per_day_df(txs_df: pd.DataFrame) -> pd.DataFrame:
    """
    Transform the transactions dataframe to aggregate the unique users
    per day

    :param txs_df: dataframe with all the transactions
    :type txs_df: pd.DataFrame
    :return: transactions function aggregated per day
    :rtype: pd.DataFrame
    """
    return txs_df.groupby("date")["sender"].nunique().reset_index()
