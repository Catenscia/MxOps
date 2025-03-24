"""
author: Etienne Wallet

This module contains Steps for token management
"""

from __future__ import annotations
from abc import ABC
from dataclasses import dataclass, field
from typing import ClassVar

from multiversx_sdk import (
    TokenManagementTransactionsFactory,
    Transaction,
    TransactionOnNetwork,
    TransactionsFactoryConfig,
    TokenManagementTransactionsOutcomeParser,
)

from mxops.config.config import Config
from mxops.data.execution_data import ScenarioData, TokenData
from mxops.enums import LogGroupEnum, TokenTypeEnum
from mxops.smart_values.mx_sdk import SmartAddress
from mxops.smart_values.native import (
    SmartBool,
    SmartBytes,
    SmartInt,
    SmartList,
    SmartStr,
)
from mxops.execution.steps.base import TransactionStep
from mxops.utils.logger import get_logger

LOGGER = get_logger(LogGroupEnum.EXEC)


@dataclass
class FungibleIssueStep(TransactionStep):
    """
    Represents the issuance of a fungible token
    """

    token_name: SmartStr
    token_ticker: SmartStr
    initial_supply: SmartInt
    num_decimals: SmartInt
    can_freeze: SmartBool = False
    can_wipe: SmartBool = False
    can_pause: SmartBool = False
    can_change_owner: SmartBool = False
    can_upgrade: SmartBool = False
    can_add_special_roles: SmartBool = False

    def build_unsigned_transaction(self) -> Transaction:
        """
        Build the transaction to issue a fungible token

        :return: transaction built
        :rtype: Transaction
        """
        LOGGER.info(
            f"Issuing fungible token named {self.token_name.get_evaluation_string()} "
            f"for {self.sender.get_evaluation_string()}"
        )
        factory_config = TransactionsFactoryConfig(Config.get_config().get("CHAIN"))
        tx_factory = TokenManagementTransactionsFactory(factory_config)
        return tx_factory.create_transaction_for_issuing_fungible(
            sender=self.sender.get_evaluated_value(),
            token_name=self.token_name.get_evaluated_value(),
            token_ticker=self.token_ticker.get_evaluated_value(),
            initial_supply=self.initial_supply.get_evaluated_value(),
            num_decimals=self.num_decimals.get_evaluated_value(),
            can_freeze=self.can_freeze.get_evaluated_value(),
            can_wipe=self.can_wipe.get_evaluated_value(),
            can_pause=self.can_pause.get_evaluated_value(),
            can_change_owner=self.can_change_owner.get_evaluated_value(),
            can_upgrade=self.can_upgrade.get_evaluated_value(),
            can_add_special_roles=self.can_add_special_roles.get_evaluated_value(),
        )

    def _post_transaction_execution(self, on_chain_tx: TransactionOnNetwork | None):
        """
        Extract the newly issued token identifier and save it within the Scenario

        :param on_chain_tx: successful transaction
        :type on_chain_tx: TransactionOnNetwork | None
        """
        if not isinstance(on_chain_tx, TransactionOnNetwork):
            raise ValueError("On chain transaction is None")
        parsed_outcome = (
            TokenManagementTransactionsOutcomeParser().parse_issue_fungible(on_chain_tx)
        )
        token_identifier = parsed_outcome[0].token_identifier
        scenario_data = ScenarioData.get()
        LOGGER.info(f"Newly issued token got the identifier {token_identifier}")
        scenario_data.add_token_data(
            TokenData(
                name=self.token_name.get_evaluated_value(),
                ticker=self.token_ticker.get_evaluated_value(),
                identifier=token_identifier,
                saved_values={},
                type=TokenTypeEnum.FUNGIBLE,
            )
        )


@dataclass
class NonFungibleIssueStep(TransactionStep):
    """
    Represents the issuance of a non fungible token
    """

    token_name: SmartStr
    token_ticker: SmartStr
    can_freeze: SmartBool = False
    can_wipe: SmartBool = False
    can_pause: SmartBool = False
    can_change_owner: SmartBool = False
    can_upgrade: SmartBool = False
    can_add_special_roles: SmartBool = False
    can_transfer_nft_create_role: SmartBool = False

    def build_unsigned_transaction(self) -> Transaction:
        """
        Build the transaction to issue a non fungible token

        :return: transaction built
        :rtype: Transaction
        """
        LOGGER.info(
            "Issuing non fungible token named "
            f"{self.token_name.get_evaluation_string()} "
            f"for {self.sender.get_evaluation_string()}"
        )
        factory_config = TransactionsFactoryConfig(Config.get_config().get("CHAIN"))
        tx_factory = TokenManagementTransactionsFactory(factory_config)
        return tx_factory.create_transaction_for_issuing_non_fungible(
            sender=self.sender.get_evaluated_value(),
            token_name=self.token_name.get_evaluated_value(),
            token_ticker=self.token_ticker.get_evaluated_value(),
            can_freeze=self.can_freeze.get_evaluated_value(),
            can_wipe=self.can_wipe.get_evaluated_value(),
            can_pause=self.can_pause.get_evaluated_value(),
            can_transfer_nft_create_role=(
                self.can_transfer_nft_create_role.get_evaluated_value()
            ),
            can_change_owner=self.can_change_owner.get_evaluated_value(),
            can_upgrade=self.can_upgrade.get_evaluated_value(),
            can_add_special_roles=self.can_add_special_roles.get_evaluated_value(),
        )

    def _post_transaction_execution(self, on_chain_tx: TransactionOnNetwork | None):
        """
        Extract the newly issued token identifier and save it within the Scenario

        :param on_chain_tx: successful transaction
        :type on_chain_tx: TransactionOnNetwork | None
        """
        if not isinstance(on_chain_tx, TransactionOnNetwork):
            raise ValueError("On chain transaction is None")
        parsed_outcome = (
            TokenManagementTransactionsOutcomeParser().parse_issue_non_fungible(
                on_chain_tx
            )
        )
        token_identifier = parsed_outcome[0].token_identifier
        scenario_data = ScenarioData.get()
        LOGGER.info(f"Newly issued token got the identifier {token_identifier}")
        scenario_data.add_token_data(
            TokenData(
                name=self.token_name.get_evaluated_value(),
                ticker=self.token_ticker.get_evaluated_value(),
                identifier=token_identifier,
                saved_values={},
                type=TokenTypeEnum.NON_FUNGIBLE,
            )
        )


@dataclass
class SemiFungibleIssueStep(TransactionStep):
    """
    Represents the issuance of a semi fungible token
    """

    token_name: SmartStr
    token_ticker: SmartStr
    can_freeze: SmartBool = False
    can_wipe: SmartBool = False
    can_pause: SmartBool = False
    can_change_owner: SmartBool = False
    can_upgrade: SmartBool = False
    can_add_special_roles: SmartBool = False
    can_transfer_nft_create_role: SmartBool = False

    def build_unsigned_transaction(self) -> Transaction:
        """
        Build the transaction to issue a semi fungible token

        :return: transaction built
        :rtype: Transaction
        """
        LOGGER.info(
            "Issuing semi fungible token named "
            f"{self.token_name.get_evaluation_string()}"
            f"for {self.sender.get_evaluation_string()}"
        )
        factory_config = TransactionsFactoryConfig(Config.get_config().get("CHAIN"))
        tx_factory = TokenManagementTransactionsFactory(factory_config)
        return tx_factory.create_transaction_for_issuing_semi_fungible(
            sender=self.sender.get_evaluated_value(),
            token_name=self.token_name.get_evaluated_value(),
            token_ticker=self.token_ticker.get_evaluated_value(),
            can_freeze=self.can_freeze.get_evaluated_value(),
            can_transfer_nft_create_role=(
                self.can_transfer_nft_create_role.get_evaluated_value()
            ),
            can_wipe=self.can_wipe.get_evaluated_value(),
            can_pause=self.can_pause.get_evaluated_value(),
            can_change_owner=self.can_change_owner.get_evaluated_value(),
            can_upgrade=self.can_upgrade.get_evaluated_value(),
            can_add_special_roles=self.can_add_special_roles.get_evaluated_value(),
        )

    def _post_transaction_execution(self, on_chain_tx: TransactionOnNetwork | None):
        """
        Extract the newly issued token identifier and save it within the Scenario

        :param on_chain_tx: successful transaction
        :type on_chain_tx: TransactionOnNetwork | None
        """
        if not isinstance(on_chain_tx, TransactionOnNetwork):
            raise ValueError("On chain transaction is None")
        parsed_outcome = (
            TokenManagementTransactionsOutcomeParser().parse_issue_semi_fungible(
                on_chain_tx
            )
        )
        token_identifier = parsed_outcome[0].token_identifier
        scenario_data = ScenarioData.get()
        LOGGER.info(f"Newly issued token got the identifier {token_identifier}")
        scenario_data.add_token_data(
            TokenData(
                name=self.token_name.get_evaluated_value(),
                ticker=self.token_ticker.get_evaluated_value(),
                identifier=token_identifier,
                saved_values={},
                type=TokenTypeEnum.SEMI_FUNGIBLE,
            )
        )


@dataclass
class MetaIssueStep(TransactionStep):
    """
    Represents the issuance of a meta fungible token
    """

    token_name: SmartStr
    token_ticker: SmartStr
    num_decimals: SmartInt
    can_freeze: SmartBool = False
    can_wipe: SmartBool = False
    can_pause: SmartBool = False
    can_change_owner: SmartBool = False
    can_upgrade: SmartBool = False
    can_add_special_roles: SmartBool = False
    can_transfer_nft_create_role: SmartBool = False

    def build_unsigned_transaction(self) -> Transaction:
        """
        Build the transaction to issue a meta token

        :return: transaction built
        :rtype: Transaction
        """
        LOGGER.info(
            f"Issuing meta token named {self.token_name.get_evaluation_string()} "
            f"for {self.sender.get_evaluation_string()}"
        )
        factory_config = TransactionsFactoryConfig(Config.get_config().get("CHAIN"))
        tx_factory = TokenManagementTransactionsFactory(factory_config)
        return tx_factory.create_transaction_for_registering_meta_esdt(
            sender=self.sender.get_evaluated_value(),
            token_name=self.token_name.get_evaluated_value(),
            token_ticker=self.token_ticker.get_evaluated_value(),
            num_decimals=self.num_decimals.get_evaluated_value(),
            can_freeze=self.can_freeze.get_evaluated_value(),
            can_wipe=self.can_wipe.get_evaluated_value(),
            can_pause=self.can_pause.get_evaluated_value(),
            can_transfer_nft_create_role=(
                self.can_transfer_nft_create_role.get_evaluated_value()
            ),
            can_change_owner=self.can_change_owner.get_evaluated_value(),
            can_upgrade=self.can_upgrade.get_evaluated_value(),
            can_add_special_roles=self.can_add_special_roles.get_evaluated_value(),
        )

    def _post_transaction_execution(self, on_chain_tx: TransactionOnNetwork | None):
        """
        Extract the newly issued token identifier and save it within the Scenario

        :param on_chain_tx: successful transaction
        :type on_chain_tx: TransactionOnNetwork | None
        """
        if not isinstance(on_chain_tx, TransactionOnNetwork):
            raise ValueError("On chain transaction is None")
        parsed_outcome = (
            TokenManagementTransactionsOutcomeParser().parse_register_meta_esdt(
                on_chain_tx
            )
        )
        token_identifier = parsed_outcome[0].token_identifier
        scenario_data = ScenarioData.get()
        LOGGER.info(f"Newly issued token got the identifier {token_identifier}")
        scenario_data.add_token_data(
            TokenData(
                name=self.token_name.get_evaluated_value(),
                ticker=self.token_ticker.get_evaluated_value(),
                identifier=token_identifier,
                saved_values={},
                type=TokenTypeEnum.META,
            )
        )


@dataclass
class ManageTokenRolesStep(TransactionStep, ABC):
    """
    A base step to set or unset roles on a token.
    Can not be used on its own: on must use the child classes
    """

    is_set: SmartBool
    token_identifier: SmartStr
    target: SmartAddress
    roles: SmartList
    ALLOWED_ROLES: ClassVar[set] = set()

    def construct_role_kwargs(self, include_missing: bool = False) -> dict[str, bool]:
        """
        construct the role kwargs needed by the factory to construct
        the tx depending on which role to set or unset

        :param include_missing: also return missing roles as False
        :type include_missing: bool
        :return: kwargs to pass to the tx factory
        :rtype: dict[str, bool]
        """
        prefix = "add_role_" if self.is_set else "remove_role_"
        roles = {}
        for role in self.roles.get_evaluated_value():
            if role not in self.ALLOWED_ROLES:
                raise ValueError(
                    f"role {role} is not in allowed roles {self.ALLOWED_ROLES}"
                )
            roles[prefix + role] = True
        if include_missing:
            for role in self.ALLOWED_ROLES:
                role_action = prefix + role
                if role_action not in roles:
                    roles[role_action] = False
        return roles


@dataclass
class ManageFungibleTokenRolesStep(ManageTokenRolesStep):
    """
    This step is used to set or unset roles for an adress on a fungible token
    """

    ALLOWED_ROLES: ClassVar[set] = {
        "local_mint",
        "local_burn",
        "esdt_transfer_role",
    }

    def build_unsigned_transaction(self) -> Transaction:
        """
        Build the transaction to set roles on a fungible token

        :return: transaction built
        :rtype: Transaction
        """
        LOGGER.info(
            f"Setting roles {self.roles.get_evaluation_string()} on the token "
            f"{self.token_identifier.get_evaluation_string()}"
            f" for {self.target.get_evaluation_string()}"
        )

        factory_config = TransactionsFactoryConfig(Config.get_config().get("CHAIN"))
        tx_factory = TokenManagementTransactionsFactory(factory_config)
        role_kwargs = self.construct_role_kwargs(include_missing=True)
        if self.is_set:
            return tx_factory.create_transaction_for_setting_special_role_on_fungible_token(  # noqa: E501 pylint: disable=C0301
                sender=self.sender.get_evaluated_value(),
                user=self.target.get_evaluated_value(),
                token_identifier=self.token_identifier.get_evaluated_value(),
                **role_kwargs,
            )
        return (
            tx_factory.create_transaction_for_unsetting_special_role_on_fungible_token(  # noqa: E501 pylint: disable=C0301
                sender=self.sender.get_evaluated_value(),
                user=self.target.get_evaluated_value(),
                token_identifier=self.token_identifier.get_evaluated_value(),
                **role_kwargs,
            )
        )


@dataclass
class ManageNonFungibleTokenRolesStep(ManageTokenRolesStep):
    """
    This step is used to set or unset roles for an adress on a non fungible token
    """

    ALLOWED_ROLES: ClassVar[set] = {
        "nft_create",
        "nft_burn",
        "nft_update_attributes",
        "nft_add_uri",
        "esdt_transfer_role",
        "nft_update",
        "esdt_modify_royalties",
        "esdt_set_new_uri",
        "esdt_modify_creator",
        "nft_recreate",
    }

    def build_unsigned_transaction(self) -> Transaction:
        """
        Build the transaction to set roles on a non fungible token

        :return: transaction built
        :rtype: Transaction
        """
        LOGGER.info(
            f"Setting roles {self.roles.get_evaluation_string()}"
            f" on the token {self.token_identifier.get_evaluation_string()}"
            f" for {self.target.get_evaluation_string()}"
        )

        factory_config = TransactionsFactoryConfig(Config.get_config().get("CHAIN"))
        tx_factory = TokenManagementTransactionsFactory(factory_config)

        role_kwargs = self.construct_role_kwargs()
        if self.is_set:
            return tx_factory.create_transaction_for_setting_special_role_on_non_fungible_token(  # noqa: E501 pylint: disable=C0301
                sender=self.sender.get_evaluated_value(),
                user=self.target.get_evaluated_value(),
                token_identifier=self.token_identifier.get_evaluated_value(),
                **role_kwargs,
            )
        return tx_factory.create_transaction_for_unsetting_special_role_on_non_fungible_token(  # noqa: E501 pylint: disable=C0301
            sender=self.sender.get_evaluated_value(),
            user=self.target.get_evaluated_value(),
            token_identifier=self.token_identifier.get_evaluated_value(),
            **role_kwargs,
        )


@dataclass
class ManageSemiFungibleTokenRolesStep(ManageTokenRolesStep):
    """
    This step is used to set or unset roles for an adress on a semi fungible token
    """

    ALLOWED_ROLES: ClassVar[set] = {
        "nft_create",
        "nft_burn",
        "nft_add_quantity",
        "esdt_transfer_role",
        "nft_update",
        "esdt_modify_royalties",
        "esdt_set_new_uri",
        "esdt_modify_creator",
        "nft_recreate",
    }

    def build_unsigned_transaction(self) -> Transaction:
        """
        Build the transaction to set roles on a non fungible token

        :return: transaction built
        :rtype: Transaction
        """
        LOGGER.info(
            f"Setting roles {self.roles.get_evaluation_string()}"
            f" on the token {self.token_identifier.get_evaluation_string()}"
            f" for {self.target.get_evaluation_string()}"
        )

        factory_config = TransactionsFactoryConfig(Config.get_config().get("CHAIN"))
        tx_factory = TokenManagementTransactionsFactory(factory_config)

        role_kwargs = self.construct_role_kwargs()
        if self.is_set:
            return tx_factory.create_transaction_for_setting_special_role_on_semi_fungible_token(  # noqa: E501 pylint: disable=C0301
                sender=self.sender.get_evaluated_value(),
                user=self.target.get_evaluated_value(),
                token_identifier=self.token_identifier.get_evaluated_value(),
                **role_kwargs,
            )
        return tx_factory.create_transaction_for_unsetting_special_role_on_semi_fungible_token(  # noqa: E501 pylint: disable=C0301
            sender=self.sender.get_evaluated_value(),
            user=self.target.get_evaluated_value(),
            token_identifier=self.token_identifier.get_evaluated_value(),
            **role_kwargs,
        )


@dataclass
class ManageMetaTokenRolesStep(ManageSemiFungibleTokenRolesStep):
    """
    This step is used to set or unset roles for an adress on a meta token
    """


@dataclass
class FungibleMintStep(TransactionStep):
    """
    This step is used to mint an additional supply for an already
    existing fungible token
    """

    token_identifier: SmartStr
    amount: SmartInt

    def build_unsigned_transaction(self) -> Transaction:
        """
        Build the transaction to mint a fungible token

        :return: transaction built
        :rtype: Transaction
        """

        LOGGER.info(
            f"Minting additional supply of {self.amount.get_evaluation_string()}"
            f" for the token {self.token_identifier.get_evaluation_string()}"
        )
        factory_config = TransactionsFactoryConfig(Config.get_config().get("CHAIN"))
        tx_factory = TokenManagementTransactionsFactory(factory_config)
        return tx_factory.create_transaction_for_local_minting(
            sender=self.sender.get_evaluated_value(),
            token_identifier=self.token_identifier.get_evaluated_value(),
            supply_to_mint=self.amount.get_evaluated_value(),
        )


@dataclass
class NonFungibleMintStep(TransactionStep):
    """
    This step is used to mint a new nonce for an already existing non fungible token.
    It can be used for NFTs, SFTs and Meta tokens.
    """

    token_identifier: SmartStr
    amount: SmartInt
    name: SmartStr = ""
    royalties: SmartInt = 0
    hash: SmartStr = ""
    attributes: SmartBytes = b""
    uris: SmartList = field(default_factory=list)

    def build_unsigned_transaction(self) -> Transaction:
        """
        Build the transaction to mint a fungible token

        :return: transaction built
        :rtype: Transaction
        """
        LOGGER.info(
            f"Minting new nonce with a supply of {self.amount.get_evaluation_string()}"
            f" for the token {self.token_identifier.get_evaluation_string()}"
        )

        factory_config = TransactionsFactoryConfig(Config.get_config().get("CHAIN"))
        tx_factory = TokenManagementTransactionsFactory(factory_config)
        return tx_factory.create_transaction_for_creating_nft(
            sender=self.sender.get_evaluated_value(),
            token_identifier=self.token_identifier.get_evaluated_value(),
            initial_quantity=self.amount.get_evaluated_value(),
            name=self.name.get_evaluated_value(),
            royalties=self.royalties.get_evaluated_value(),
            hash=self.hash.get_evaluated_value(),
            attributes=self.attributes.get_evaluated_value(),
            uris=self.uris.get_evaluated_value(),
        )

    def _post_transaction_execution(self, on_chain_tx: TransactionOnNetwork | None):
        """
        Extract the newly issued nonce and print it

        :param on_chain_tx: successful transaction
        :type on_chain_tx: TransactionOnNetwork | None
        """
        if not isinstance(on_chain_tx, TransactionOnNetwork):
            return
        parsed_outcome = TokenManagementTransactionsOutcomeParser().parse_nft_create(
            on_chain_tx
        )
        new_nonce = parsed_outcome[0].nonce
        LOGGER.info(f"Newly issued nonce is {new_nonce}")
