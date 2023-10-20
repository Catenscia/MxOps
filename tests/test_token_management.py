import json
from pathlib import Path

from multiversx_sdk_network_providers.transactions import TransactionOnNetwork

from mxops.execution import token_management


def test_token_identifier_extraction(test_data_folder_path: Path):
    # Given
    with open(test_data_folder_path / "api_responses" / "meta_issue.json") as file:
        on_chain_tx = TransactionOnNetwork.from_proxy_http_response(**json.load(file))

    # When
    new_token_identifier = token_management.extract_new_token_identifier(on_chain_tx)

    # Then
    assert new_token_identifier == "META-bdbf88"


def test_nonce_extraction(test_data_folder_path: Path):
    # Given
    with open(test_data_folder_path / "api_responses" / "meta_nonce_mint.json") as file:
        on_chain_tx = TransactionOnNetwork.from_proxy_http_response(**json.load(file))

    # When
    new_nonce = token_management.extract_new_nonce(on_chain_tx)

    # Then
    assert new_nonce == 2
