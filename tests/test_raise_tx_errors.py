import json
from pathlib import Path

from multiversx_sdk.network_providers.http_resources import (
    transaction_from_proxy_response,
)

from mxops.execution.network import raise_on_errors
from mxops import errors


def test_out_of_gas(test_data_folder_path: Path):
    # Given
    with open(test_data_folder_path / "api_responses" / "out_of_gas.json") as file:
        tx = transaction_from_proxy_response(**json.load(file))

    # When

    # Then
    try:
        raise_on_errors(tx)
        raise RuntimeError("`InternalVmExecutionError` was expected but was not raised")
    except errors.InternalVmExecutionError:
        pass


def test_not_enough_esdt(test_data_folder_path: Path):
    # Given
    with open(test_data_folder_path / "api_responses" / "not_enough_esdt.json") as file:
        tx = transaction_from_proxy_response(**json.load(file))

    # When

    # Then
    try:
        raise_on_errors(tx)
        raise RuntimeError("`InvalidTransactionError` was expected but was not raised")
    except errors.InvalidTransactionError:
        pass


def test_vm_error(test_data_folder_path: Path):
    # Given
    with open(test_data_folder_path / "api_responses" / "vm_error.json") as file:
        tx = transaction_from_proxy_response(**json.load(file))

    # When

    # Then
    try:
        raise_on_errors(tx)
        raise RuntimeError("`InternalVmExecutionError` was expected but was not raised")
    except errors.InternalVmExecutionError:
        pass
