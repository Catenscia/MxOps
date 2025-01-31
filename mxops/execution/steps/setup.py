"""
author: Etienne Wallet

This module contains Steps used to setup environnement, chain or workflow
"""

from dataclasses import dataclass, field
import os

from mxops import errors
from mxops.execution import utils
from mxops.execution.smart_values import SmartInt, SmartPath, SmartValue
from mxops.execution.steps.base import Step
from mxops.utils.logger import get_logger
from mxops.utils.wallets import generate_pem_wallet


LOGGER = get_logger("setup steps")


@dataclass
class GenerateWalletsStep(Step):
    """
    Represents a step to generate some MultiversX wallets
    For now, only pem wallets are supported
    """

    save_folder: SmartPath
    wallets: SmartValue
    shard: SmartInt | None = field(default=None)

    def _execute(self):
        """
        Create the wanted wallets at the designated location

        """
        save_folder = self.save_folder.get_evaluated_value()
        save_folder.mkdir(parents=True, exist_ok=True)
        wallets = self.wallets.get_evaluated_value()
        shard = None if self.shard is None else self.shard.get_evaluated_value()
        if isinstance(wallets, int):
            n_wallets = wallets
            names = [None] * n_wallets
        elif isinstance(wallets, list):
            n_wallets = len(wallets)
            names = wallets
        else:
            raise ValueError(
                "the wallets argument must be of type int or list[str], "
                f"got {type(wallets)}"
            )
        for i, name in enumerate(names):
            pem_wallet, wallet_address = generate_pem_wallet(shard)
            if name is None:
                wallet_name = wallet_address.to_bech32()
            else:
                wallet_name = utils.retrieve_value_from_any(name)
            wallet_path = save_folder / f"{wallet_name}.pem"
            if os.path.isfile(wallet_path.as_posix()):
                raise errors.WalletAlreadyExist(wallet_path)

            pem_wallet.save(wallet_path)
            LOGGER.info(
                f"Wallet n°{i + 1}/{n_wallets} generated with address "
                f"{wallet_address.to_bech32()} at {wallet_path}"
            )
