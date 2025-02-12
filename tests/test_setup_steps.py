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
