"""
author: Etienne Wallet

This modules contains missing transaction builders classes from multiversx_sdk_core.
Idealy, a PR should be made to propose them to the MultiversX team: in the mean time,
here they are
"""
from abc import abstractmethod
from dataclasses import dataclass
import itertools
from typing import Dict, List, Optional, Protocol

from multiversx_sdk_core.serializer import arg_to_string, args_to_strings
from multiversx_sdk_core.interfaces import (
    IAddress,
    IGasLimit,
    IGasPrice,
    INonce,
    ITokenIdentifier,
    ITransactionValue,
)
from multiversx_sdk_core.transaction_builders.transaction_builder import (
    ITransactionBuilderConfiguration,
    TransactionBuilder,
)
from multiversx_sdk_core.transaction_builders.esdt_builders import (
    IESDTIssueConfiguration,
)
from multiversx_sdk_core.transaction_builders import (
    DefaultTransactionBuildersConfiguration,
)

from mxops.config.config import Config


@dataclass
class MyDefaultTransactionBuildersConfiguration(
    DefaultTransactionBuildersConfiguration
):
    """
    Extend the default configuration of multiversx_sdk_core with more parameters
    """

    gas_limit_esdt_roles = 60000000
    gas_limit_mint = 300000
    gas_limit_store_per_byte = 50000


class TokenIssueBuilder(TransactionBuilder):
    """
    Base class to construct a token issuance transaction
    """

    TRUE_BY_DEFAULT_PROPERTIES = ("canUpgrade", "canAddSpecialRoles")

    def __init__(
        self,
        config: IESDTIssueConfiguration,
        issuer: IAddress,
        issuance_endpoint: str,
        nonce: Optional[INonce] = None,
        value: Optional[ITransactionValue] = None,
        gas_limit: Optional[IGasLimit] = None,
        gas_price: Optional[IGasPrice] = None,
    ) -> None:
        super().__init__(config, nonce, value, gas_limit, gas_price)
        self.value = config.issue_cost
        self.gas_limit_esdt_issue = config.gas_limit_esdt_issue

        self.sender = issuer
        self.receiver = config.esdt_contract_address

        self.issuance_endpoint = issuance_endpoint

    def _estimate_execution_gas(self) -> IGasLimit:
        return self.gas_limit_esdt_issue

    @abstractmethod
    def get_token_args(self) -> List:
        pass

    @abstractmethod
    def get_token_properties(self) -> Dict:
        pass

    def _build_payload_parts(self) -> List[str]:
        """
        build the payload parts for the transaction

        :return: payload parts
        :rtype: List[str]
        """
        properties_args = []
        for prop, value in self.get_token_properties().items():
            if prop in self.TRUE_BY_DEFAULT_PROPERTIES:
                if not value:
                    properties_args.append((prop, "false"))
                continue
            if value:
                properties_args.append((prop, "true"))
        chained_properties_args = list(itertools.chain(*properties_args))
        return [
            self.issuance_endpoint,
            *args_to_strings(self.get_token_args()),
            *args_to_strings(chained_properties_args),
        ]


class FungibleTokenIssueBuilder(TokenIssueBuilder):
    """
    Class to construct a fungible issuance transaction
    This class should be included to multiversx_sdk_core.transaction_builders
    """

    def __init__(
        self,
        config: IESDTIssueConfiguration,
        issuer: IAddress,
        token_name: str,
        token_ticker: str,
        initial_supply: int,
        num_decimals: int,
        can_freeze: bool = False,
        can_wipe: bool = False,
        can_pause: bool = False,
        can_mint: bool = False,
        can_burn: bool = False,
        can_change_owner: bool = False,
        can_upgrade: bool = False,
        can_add_special_roles: bool = False,
        nonce: Optional[INonce] = None,
        value: Optional[ITransactionValue] = None,
        gas_limit: Optional[IGasLimit] = None,
        gas_price: Optional[IGasPrice] = None,
    ) -> None:
        super().__init__(config, issuer, "issue", nonce, value, gas_limit, gas_price)

        self.token_name = token_name
        self.token_ticker = token_ticker
        self.initial_supply = initial_supply
        self.num_decimals = num_decimals
        self.can_freeze = can_freeze
        self.can_wipe = can_wipe
        self.can_pause = can_pause
        self.can_mint = can_mint
        self.can_burn = can_burn
        self.can_change_owner = can_change_owner
        self.can_upgrade = can_upgrade
        self.can_add_special_roles = can_add_special_roles

    def get_token_args(self) -> List:
        return [
            self.token_name,
            self.token_ticker,
            self.initial_supply,
            self.num_decimals,
        ]

    def get_token_properties(self) -> List:
        return {
            "canFreeze": self.can_freeze,
            "canWipe": self.can_wipe,
            "canPause": self.can_pause,
            "canMint": self.can_mint,
            "canBurn": self.can_burn,
            "canChangeOwner": self.can_change_owner,
            "canUpgrade": self.can_upgrade,
            "canAddSpecialRoles": self.can_add_special_roles,
        }


class NonFungibleTokenIssueBuilder(TokenIssueBuilder):
    """
    Class to construct a non fungible issuance transaction
    This class should be included to multiversx_sdk_core.transaction_builders
    """

    def __init__(
        self,
        config: IESDTIssueConfiguration,
        issuer: IAddress,
        token_name: str,
        token_ticker: str,
        can_freeze: bool = False,
        can_wipe: bool = False,
        can_pause: bool = False,
        can_change_owner: bool = False,
        can_upgrade: bool = False,
        can_add_special_roles: bool = False,
        can_transfer_nft_create_role: bool = False,
        nonce: Optional[INonce] = None,
        value: Optional[ITransactionValue] = None,
        gas_limit: Optional[IGasLimit] = None,
        gas_price: Optional[IGasPrice] = None,
    ) -> None:
        super().__init__(
            config, issuer, "issueNonFungible", nonce, value, gas_limit, gas_price
        )

        self.token_name = token_name
        self.token_ticker = token_ticker
        self.can_freeze = can_freeze
        self.can_wipe = can_wipe
        self.can_pause = can_pause
        self.can_change_owner = can_change_owner
        self.can_upgrade = can_upgrade
        self.can_add_special_roles = can_add_special_roles
        self.can_transfer_nft_create_role = can_transfer_nft_create_role

    def get_token_args(self) -> List:
        return [self.token_name, self.token_ticker]

    def get_token_properties(self) -> List:
        return {
            "canFreeze": self.can_freeze,
            "canWipe": self.can_wipe,
            "canPause": self.can_pause,
            "canChangeOwner": self.can_change_owner,
            "canUpgrade": self.can_upgrade,
            "canAddSpecialRoles": self.can_add_special_roles,
            "canTransferNFTCreateRole": self.can_transfer_nft_create_role,
        }


class SemiFungibleTokenIssueBuilder(TokenIssueBuilder):
    """
    Class to construct a semi fungible issuance transaction
    This class should be included to multiversx_sdk_core.transaction_builders
    """

    def __init__(
        self,
        config: IESDTIssueConfiguration,
        issuer: IAddress,
        token_name: str,
        token_ticker: str,
        can_freeze: bool = False,
        can_wipe: bool = False,
        can_pause: bool = False,
        can_change_owner: bool = False,
        can_upgrade: bool = False,
        can_add_special_roles: bool = False,
        can_transfer_nft_create_role: bool = False,
        nonce: Optional[INonce] = None,
        value: Optional[ITransactionValue] = None,
        gas_limit: Optional[IGasLimit] = None,
        gas_price: Optional[IGasPrice] = None,
    ) -> None:
        super().__init__(
            config, issuer, "issueSemiFungible", nonce, value, gas_limit, gas_price
        )

        self.token_name = token_name
        self.token_ticker = token_ticker
        self.can_freeze = can_freeze
        self.can_wipe = can_wipe
        self.can_pause = can_pause
        self.can_change_owner = can_change_owner
        self.can_upgrade = can_upgrade
        self.can_add_special_roles = can_add_special_roles
        self.can_transfer_nft_create_role = can_transfer_nft_create_role

    def get_token_args(self) -> List:
        return [self.token_name, self.token_ticker]

    def get_token_properties(self) -> List:
        return {
            "canFreeze": self.can_freeze,
            "canWipe": self.can_wipe,
            "canPause": self.can_pause,
            "canChangeOwner": self.can_change_owner,
            "canUpgrade": self.can_upgrade,
            "canAddSpecialRoles": self.can_add_special_roles,
            "canTransferNFTCreateRole": self.can_transfer_nft_create_role,
        }


class MetaFungibleTokenIssueBuilder(TokenIssueBuilder):
    """
    Class to construct a meta issuance transaction
    This class should be included to multiversx_sdk_core.transaction_builders
    """

    def __init__(
        self,
        config: IESDTIssueConfiguration,
        issuer: IAddress,
        token_name: str,
        token_ticker: str,
        num_decimals: int,
        can_freeze: bool = False,
        can_wipe: bool = False,
        can_pause: bool = False,
        can_change_owner: bool = False,
        can_upgrade: bool = False,
        can_add_special_roles: bool = False,
        can_transfer_nft_create_role: bool = False,
        nonce: Optional[INonce] = None,
        value: Optional[ITransactionValue] = None,
        gas_limit: Optional[IGasLimit] = None,
        gas_price: Optional[IGasPrice] = None,
    ) -> None:
        super().__init__(
            config, issuer, "registerMetaESDT", nonce, value, gas_limit, gas_price
        )

        self.token_name = token_name
        self.token_ticker = token_ticker
        self.num_decimals = num_decimals
        self.can_freeze = can_freeze
        self.can_wipe = can_wipe
        self.can_pause = can_pause
        self.can_change_owner = can_change_owner
        self.can_upgrade = can_upgrade
        self.can_add_special_roles = can_add_special_roles
        self.can_transfer_nft_create_role = can_transfer_nft_create_role

    def get_token_args(self) -> List:
        return [self.token_name, self.token_ticker, self.num_decimals]

    def get_token_properties(self) -> List:
        return {
            "canFreeze": self.can_freeze,
            "canWipe": self.can_wipe,
            "canPause": self.can_pause,
            "canChangeOwner": self.can_change_owner,
            "canUpgrade": self.can_upgrade,
            "canAddSpecialRoles": self.can_add_special_roles,
            "canTransferNFTCreateRole": self.can_transfer_nft_create_role,
        }


class IESDTRolesConfiguration(ITransactionBuilderConfiguration, Protocol):
    gas_limit_esdt_roles: IGasLimit
    esdt_contract_address: IAddress


class ManageTokenRolesBuilder(TransactionBuilder):
    """
    Class to construct the transaction to set or unset roles
    for an address on an account
    """

    def __init__(
        self,
        config: IESDTRolesConfiguration,
        sender: IAddress,
        is_set: bool,
        token_identifier: ITokenIdentifier,
        target: IAddress,
        roles: List[str],
        nonce: Optional[INonce] = None,
        value: Optional[ITransactionValue] = None,
        gas_limit: Optional[IGasLimit] = None,
        gas_price: Optional[IGasPrice] = None,
    ) -> None:
        super().__init__(config, nonce, value, gas_limit, gas_price)
        self.gas_limit_esdt_roles = config.gas_limit_esdt_roles

        self.sender = sender
        self.receiver = config.esdt_contract_address

        self.is_set = is_set
        self.target = target
        self.token_identifier = token_identifier
        self.roles = roles

    def _estimate_execution_gas(self) -> IGasLimit:
        return self.gas_limit_esdt_roles

    def _build_payload_parts(self) -> List[str]:
        endpoint = "setSpecialRole" if self.is_set else "unsetSpecialRole"
        return [
            endpoint,
            arg_to_string(self.token_identifier),
            arg_to_string(self.target),
            *args_to_strings(self.roles),
        ]


class IESDTMintConfiguration(ITransactionBuilderConfiguration, Protocol):
    gas_limit_mint: IGasLimit
    gas_limit_store_per_byte: IGasLimit


class FungibleMintBuilder(TransactionBuilder):
    """
    Class to create the transaction to mint additional supply for
    an already existing fungible token
    """

    def __init__(
        self,
        config: IESDTMintConfiguration,
        sender: IAddress,
        token_identifier: ITokenIdentifier,
        amount_as_integer: int,
        nonce: Optional[INonce] = None,
        value: Optional[ITransactionValue] = None,
        gas_limit: Optional[IGasLimit] = None,
        gas_price: Optional[IGasPrice] = None,
    ) -> None:
        super().__init__(config, nonce, value, gas_limit, gas_price)
        self.gas_limit_mint = config.gas_limit_mint

        self.sender = sender
        self.receiver = sender
        self.token_identifier = token_identifier
        self.amount_as_integer = amount_as_integer

    def _estimate_execution_gas(self) -> IGasLimit:
        return self.gas_limit_mint

    def _build_payload_parts(self) -> List[str]:
        return [
            "ESDTLocalMint",
            arg_to_string(self.token_identifier),
            arg_to_string(self.amount_as_integer),
        ]


class NonFungibleMintBuilder(TransactionBuilder):
    """
    Builder to construct the transaction to mint a new non fungible token
    (ide a new nonce).
    This can be used for NFTs, SFTs and Meta tokens.
    """

    def __init__(
        self,
        config: IESDTMintConfiguration,
        sender: IAddress,
        token_identifier: ITokenIdentifier,
        amount_as_integer: int,
        name: str,
        royalties: int,
        hash: str,
        attributes: str,
        uris: List[str],
        nonce: Optional[INonce] = None,
        value: Optional[ITransactionValue] = None,
        gas_limit: Optional[IGasLimit] = None,
        gas_price: Optional[IGasPrice] = None,
    ) -> None:
        super().__init__(config, nonce, value, gas_limit, gas_price)
        self.gas_limit_mint = config.gas_limit_mint
        self.gas_limit_per_byte = config.gas_limit_per_byte
        self.gas_limit_store_per_byte = config.gas_limit_store_per_byte

        self.sender = sender
        self.receiver = sender
        self.token_identifier = token_identifier
        self.amount_as_integer = amount_as_integer
        self.name = name
        self.royalties = royalties
        self.hash = hash
        self.attributes = attributes
        self.uris = uris

    def _estimate_execution_gas(self) -> IGasLimit:
        n_data_bytes = len(self.build_payload().data)
        additionnal_gas = n_data_bytes * (
            self.gas_limit_per_byte + self.gas_limit_store_per_byte
        )
        return self.gas_limit_mint + additionnal_gas

    def _build_payload_parts(self) -> List[str]:
        formatted_uris = args_to_strings(self.uris) if len(self.uris) else [""]
        return [
            "ESDTNFTCreate",
            arg_to_string(self.token_identifier),
            arg_to_string(self.amount_as_integer),
            arg_to_string(self.name),
            arg_to_string(self.royalties),
            arg_to_string(self.hash),
            arg_to_string(self.attributes),
            *formatted_uris,
        ]


def get_builder_config() -> DefaultTransactionBuildersConfiguration:
    """
    Return an instance of the config for the builder

    :return: config for the builder
    :rtype: DefaultTransactionBuildersConfiguration
    """
    config = Config.get_config()
    return MyDefaultTransactionBuildersConfiguration(chain_id=config.get("CHAIN"))
