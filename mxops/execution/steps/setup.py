"""
author: Etienne Wallet

This module contains Steps used to setup environnement, chain or workflow
"""

from dataclasses import dataclass, field
import os
from typing import ClassVar

import requests

from mxops import errors
from mxops.common.providers import MyProxyNetworkProvider
from mxops.config.config import Config
from mxops.data.execution_data import ScenarioData
from mxops.enums import NetworkEnum
from mxops.execution import utils
from mxops.execution.smart_values import SmartInt, SmartPath, SmartValue
from mxops.execution.smart_values.mx_sdk import SmartAddresses
from mxops.execution.steps.base import Step
from mxops.execution.steps.transactions import TransferStep
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
        scenario_data = ScenarioData.get()
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
            scenario_data.set_value(
                f"{wallet_name}.address", wallet_address.to_bech32()
            )
            LOGGER.info(
                f"Wallet n°{i + 1}/{n_wallets} generated with address "
                f"{wallet_address.to_bech32()} at {wallet_path}"
            )


@dataclass
class R3D4FaucetStep(Step):
    """
    Represents a step to request some EGLD from the r3d4 faucet
    """

    targets: SmartAddresses
    ALLOWED_NETWORKS: ClassVar[set] = (NetworkEnum.DEV, NetworkEnum.TEST)

    def get_egld_details(self) -> dict:
        """
        Request r3d4 for the details regarding the EGLD token faucet

        :return: token id, max amount and available
        :rtype: Tuple[int, int]
        """
        config = Config.get_config()
        url = f"{config.get('R3D4_API')}/faucet/tokens"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        chain = config.get("CHAIN")
        for token_data in data:
            if token_data["network"] != chain:
                continue
            if token_data["identifier"] in ("xEGLD", "dEGLD", "EGLD", "tEGLD"):
                return token_data
        raise errors.TokenNotFound("Could not found EGLD in the faucet")

    def _execute(self):
        """
        Seach for the r3d4 token id of EGLD in the current network and
        ask for EGLD from the faucet
        """
        scenario_data = ScenarioData.get()
        if scenario_data.network not in self.ALLOWED_NETWORKS:
            raise errors.WrongNetworkForStep(
                scenario_data.network, self.ALLOWED_NETWORKS
            )
        egld_details = self.get_egld_details()
        request_amount = float(egld_details["max"])
        for target in self.targets.get_evaluated_value():
            LOGGER.info(
                f"Requesting {request_amount} {egld_details['identifier']}"
                f" from r3d4 faucet for {target.to_bech32()}"
            )
            self.request_faucet(
                target.to_bech32(), egld_details["id"], str(request_amount)
            )

    def request_faucet(self, bech32: str, token_id: str, amount: str):
        """
        Request the faucet for a token amount for an address

        :param bech32: address where to receive the tokens
        :type bech32: str
        :param token_id: r3d4 token id to recieve
        :type token_id: int
        :param amount: amount of token to recieve, with decimal
        :type amount: str
        """
        config = Config.get_config()
        url = f"{config.get('R3D4_API')}/faucet/list"
        headers = {
            "accept": "application/json",
        }
        data = {
            "formdata": {
                "network": config.get("CHAIN"),
                "token": token_id,
                "address": bech32,
                "amount": amount,
            }
        }
        response = requests.post(url, json=data, headers=headers, timeout=5)
        response.raise_for_status()
        return_data = response.json()
        if "error" in return_data:
            raise errors.FaucetFailed(return_data["error"])
        LOGGER.info(f"Response from faucet: {return_data['success']}")


@dataclass
class ChainSimulatorFaucetStep(Step):
    """
    Represents a step to request some EGLD from the chain-simulator faucet
    (aka initial wallets of the chain simulator)
    """

    targets: SmartAddresses
    amount: SmartInt
    ALLOWED_NETWORKS: ClassVar[set] = (NetworkEnum.CHAIN_SIMULATOR,)

    def _execute(self):
        """
        Retrieve the initial wallets of the chain simulator and
        make them send some funds
        """
        scenario_data = ScenarioData.get()
        if scenario_data.network not in self.ALLOWED_NETWORKS:
            raise errors.WrongNetworkForStep(
                scenario_data.network, self.ALLOWED_NETWORKS
            )
        proxy = MyProxyNetworkProvider()
        initial_wallet_data = proxy.get_initial_wallets()
        sender = initial_wallet_data["balanceWallets"]["0"]["address"]["bech32"]
        for target in self.targets.get_evaluated_value():
            egld_transfer_step = TransferStep(
                sender=sender, receiver=target, value=self.amount.get_evaluated_value()
            )
            egld_transfer_step.execute()
