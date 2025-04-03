from mxops.utils.msc import get_account_link, get_tx_link


def test_transaction_link():
    # Given
    tx_hash = "3519ff7dd9ed71fb140e2b79a51cfeb9e90df749504bb436ebb697a30f8afcf5"

    # When
    link = get_tx_link(tx_hash)

    # Then
    assert (
        link
        == "http://localhost:3002/transactions/3519ff7dd9ed71fb140e2b79a51cfeb9e90df749504bb436ebb697a30f8afcf5"  # noqa
    )


def test_account_link():
    # Given
    bech32 = "erd1jkd354c4mz9cfp8vjh2cvv2vtc7fg4klfktrqp8c627r6x86sa8qquzu45"

    # When
    link = get_account_link(bech32)

    # Then
    assert (
        link
        == "http://localhost:3002/accounts/erd1jkd354c4mz9cfp8vjh2cvv2vtc7fg4klfktrqp8c627r6x86sa8qquzu45"  # noqa
    )
