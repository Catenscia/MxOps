import os
from pathlib import Path
import shutil

from multiversx_sdk import Account
from mxops.execution.steps import GenerateWalletsStep


def test_generate_n_wallet_step():
    # Given
    step = GenerateWalletsStep("./tests/data/TEMP_UNIT_TEST/wallets/folder", 3)

    # When
    step.execute()

    # Then
    save_folder = Path("./tests/data/TEMP_UNIT_TEST/wallets/folder")
    files = os.listdir(save_folder)
    assert len(files) == 3
    for file in files:
        account = Account.new_from_pem(save_folder / file)
        bech32, extension = file.split(".")
        assert bech32 == account.address.to_bech32()
        assert extension == "pem"

    shutil.rmtree("./tests/data/TEMP_UNIT_TEST")


def test_generate_named_wallet_step():
    # Given
    step = GenerateWalletsStep(
        "./tests/data/TEMP_UNIT_TEST/wallets/folder", ["charles", "david"]
    )

    # When
    step.execute()

    # Then
    save_folder = Path("./tests/data/TEMP_UNIT_TEST/wallets/folder")
    files = os.listdir(save_folder)
    assert set(files) == {"charles.pem", "david.pem"}
    for file in files:
        _ = Account.new_from_pem(save_folder / file)

    shutil.rmtree("./tests/data/TEMP_UNIT_TEST")


def test_generate_keystore_wallet_step():
    # Given
    os.environ["TEST_WALLET_PASSWORD"] = "test_password_123"
    step = GenerateWalletsStep(
        "./tests/data/TEMP_UNIT_TEST/wallets/keystore_folder",
        ["alice_ks", "bob_ks"],
        format="keystore",
        password_env_var="TEST_WALLET_PASSWORD",
    )

    # When
    step.execute()

    # Then
    save_folder = Path("./tests/data/TEMP_UNIT_TEST/wallets/keystore_folder")
    files = os.listdir(save_folder)
    assert set(files) == {"alice_ks.json", "bob_ks.json"}
    for file in files:
        _ = Account.new_from_keystore(
            save_folder / file, os.environ["TEST_WALLET_PASSWORD"]
        )

    # Cleanup
    shutil.rmtree("./tests/data/TEMP_UNIT_TEST")
    del os.environ["TEST_WALLET_PASSWORD"]


def test_generate_n_keystore_wallet_step():
    # Given
    os.environ["TEST_WALLET_PASSWORD"] = "test_password_456"
    step = GenerateWalletsStep(
        "./tests/data/TEMP_UNIT_TEST/wallets/keystore_n",
        2,
        format="keystore",
        password_env_var="TEST_WALLET_PASSWORD",
    )

    # When
    step.execute()

    # Then
    save_folder = Path("./tests/data/TEMP_UNIT_TEST/wallets/keystore_n")
    files = os.listdir(save_folder)
    assert len(files) == 2
    for file in files:
        account = Account.new_from_keystore(
            save_folder / file, os.environ["TEST_WALLET_PASSWORD"]
        )
        name, extension = file.rsplit(".", 1)
        assert name == account.address.to_bech32()
        assert extension == "json"

    # Cleanup
    shutil.rmtree("./tests/data/TEMP_UNIT_TEST")
    del os.environ["TEST_WALLET_PASSWORD"]
