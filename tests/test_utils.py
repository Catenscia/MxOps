from multiversx_sdk_core import Address
import pytest

from mxops.execution.utils import get_address_instance


@pytest.mark.parametrize(
    "address_str, expected_result",
    [
        (
            "erd1qqqqqqqqqqqqqpgqdmq43snzxutandvqefxgj89r6fh528v9dwnswvgq9t",
            Address.from_bech32(
                "erd1qqqqqqqqqqqqqpgqdmq43snzxutandvqefxgj89r6fh528v9dwnswvgq9t",
            ),
        ),
        (
            "%my_test_contract.address",
            Address.from_bech32(
                "erd1qqqqqqqqqqqqqpgqdmq43snzxutandvqefxgj89r6fh528v9dwnswvgq9t",
            ),
        ),
        (
            "my_test_contract",
            Address.from_bech32(
                "erd1qqqqqqqqqqqqqpgqdmq43snzxutandvqefxgj89r6fh528v9dwnswvgq9t",
            ),
        ),
    ],
)
def test_get_address_instance(address_str: str, expected_result: Address):
    # Given
    # When
    result = get_address_instance(address_str)
    # Then
    assert expected_result.bech32() == result.bech32()
