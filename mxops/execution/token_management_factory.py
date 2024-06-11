"""
author: Etienne Wallet

This modules contains missing factory methods from multiversx_sdk_core.
Idealy, a PR should be made to propose them to the MultiversX team: in the mean time,
here they are
"""

from typing import List
from multiversx_sdk_core.interfaces import IAddress
from multiversx_sdk_core.serializer import arg_to_string
from multiversx_sdk_core.transaction_factories.transaction_builder import (
    TransactionBuilder,
)
from multiversx_sdk_core.transaction import Transaction
from multiversx_sdk_core.transaction_factories import TokenManagementTransactionsFactory


class MyTokenManagementTransactionsFactory(TokenManagementTransactionsFactory):
    def create_transaction_for_setting_special_role_on_fungible_token(
        self,
        sender: IAddress,
        user: IAddress,
        token_identifier: str,
        add_role_local_mint: bool,
        add_role_local_burn: bool,
        add_transfer_role: bool,
    ) -> Transaction:
        parts: List[str] = [
            "setSpecialRole",
            arg_to_string(token_identifier),
            user.to_hex(),
            *([arg_to_string("ESDTRoleLocalMint")] if add_role_local_mint else []),
            *([arg_to_string("ESDTRoleLocalBurn")] if add_role_local_burn else []),
            *([arg_to_string("ESDTTransferRole")] if add_transfer_role else []),
        ]

        return TransactionBuilder(
            config=self._config,
            sender=sender,
            receiver=self._config.esdt_contract_address,
            amount=None,
            gas_limit=self._config.gas_limit_set_special_role,
            add_data_movement_gas=True,
            data_parts=parts,
        ).build()

    def create_transaction_for_unsetting_special_role_on_fungible_token(
        self,
        sender: IAddress,
        user: IAddress,
        token_identifier: str,
        remove_role_local_mint: bool,
        remove_role_local_burn: bool,
        remove_transfer_role: bool,
    ) -> Transaction:
        parts: List[str] = [
            "unsetSpecialRole",
            arg_to_string(token_identifier),
            user.to_hex(),
            *([arg_to_string("ESDTRoleLocalMint")] if remove_role_local_mint else []),
            *([arg_to_string("ESDTRoleLocalBurn")] if remove_role_local_burn else []),
            *([arg_to_string("ESDTTransferRole")] if remove_transfer_role else []),
        ]

        return TransactionBuilder(
            config=self._config,
            sender=sender,
            receiver=self._config.esdt_contract_address,
            amount=None,
            gas_limit=self._config.gas_limit_set_special_role,
            add_data_movement_gas=True,
            data_parts=parts,
        ).build()

    def create_transaction_for_unsetting_special_role_on_semi_fungible_token(
        self,
        sender: IAddress,
        user: IAddress,
        token_identifier: str,
        remove_role_nft_create: bool,
        remove_role_nft_burn: bool,
        remove_role_nft_add_quantity: bool,
        remove_role_esdt_transfer_role: bool,
    ) -> Transaction:
        parts: List[str] = [
            "unsetSpecialRole",
            arg_to_string(token_identifier),
            user.to_hex(),
            *([arg_to_string("ESDTRoleNFTCreate")] if remove_role_nft_create else []),
            *([arg_to_string("ESDTRoleNFTBurn")] if remove_role_nft_burn else []),
            *(
                [arg_to_string("ESDTRoleNFTAddQuantity")]
                if remove_role_nft_add_quantity
                else []
            ),
            *(
                [arg_to_string("ESDTTransferRole")]
                if remove_role_esdt_transfer_role
                else []
            ),
        ]

        return TransactionBuilder(
            config=self._config,
            sender=sender,
            receiver=self._config.esdt_contract_address,
            amount=None,
            gas_limit=self._config.gas_limit_set_special_role,
            add_data_movement_gas=True,
            data_parts=parts,
        ).build()

    def create_transaction_for_unsetting_special_role_on_non_fungible_token(
        self,
        sender: IAddress,
        user: IAddress,
        token_identifier: str,
        remove_role_nft_create: bool,
        remove_role_nft_burn: bool,
        remove_role_nft_update_attributes: bool,
        remove_role_nft_add_uri: bool,
        remove_role_esdt_transfer_role: bool,
    ) -> Transaction:
        parts: List[str] = [
            "unsetSpecialRole",
            arg_to_string(token_identifier),
            user.to_hex(),
            *([arg_to_string("ESDTRoleNFTCreate")] if remove_role_nft_create else []),
            *([arg_to_string("ESDTRoleNFTBurn")] if remove_role_nft_burn else []),
            *(
                [arg_to_string("ESDTRoleNFTUpdateAttributes")]
                if remove_role_nft_update_attributes
                else []
            ),
            *([arg_to_string("ESDTRoleNFTAddURI")] if remove_role_nft_add_uri else []),
            *(
                [arg_to_string("ESDTTransferRole")]
                if remove_role_esdt_transfer_role
                else []
            ),
        ]

        return TransactionBuilder(
            config=self._config,
            sender=sender,
            receiver=self._config.esdt_contract_address,
            amount=None,
            gas_limit=self._config.gas_limit_set_special_role,
            add_data_movement_gas=True,
            data_parts=parts,
        ).build()
