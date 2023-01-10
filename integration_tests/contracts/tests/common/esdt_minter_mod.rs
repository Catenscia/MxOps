elrond_wasm::imports!();
elrond_wasm::derive_imports!();

use elrond_wasm_debug::{
    managed_biguint, managed_token_id, rust_biguint, testing_framework::ContractObjWrapper,
    tx_mock::TxResult, DebugApi,
};
use esdt_minter::EsdtMinter;

use super::blockchain_mod::*;

pub fn setup_esdt_minter<EsdtMinterObjBuilder>(
    sc_builder: EsdtMinterObjBuilder,
    blockchain_setup: &mut BlockchainSetup,
) -> ContractObjWrapper<esdt_minter::ContractObj<DebugApi>, EsdtMinterObjBuilder>
where
    EsdtMinterObjBuilder: 'static + Copy + Fn() -> esdt_minter::ContractObj<DebugApi>,
{
    let blockchain_wrapper = &mut blockchain_setup.blockchain_wrapper;
    let rust_zero = rust_biguint!(0u64);

    let esdt_minter_wrapper = blockchain_wrapper.create_sc_account(
        &rust_zero,
        Some(&blockchain_setup.owner_address),
        sc_builder,
        PIGGY_BANK_WASM_PATH,
    );

    // deploy contract
    blockchain_wrapper
        .execute_tx(
            &blockchain_setup.owner_address,
            &esdt_minter_wrapper,
            &rust_zero,
            |sc| {
                sc.init(ESDT_MINTER_INTEREST_PERCENTAGE);
            },
        )
        .assert_ok();

    // fake token issuance

    let token_roles = [
        EsdtLocalRole::NftCreate,
        EsdtLocalRole::NftAddQuantity,
        EsdtLocalRole::NftBurn,
        EsdtLocalRole::Mint,
    ];

    blockchain_wrapper.set_esdt_local_roles(
        esdt_minter_wrapper.address_ref(),
        PIGGY_TOKEN_IDENTIFIER,
        &token_roles[..],
    );

    blockchain_wrapper
        .execute_tx(
            &blockchain_setup.owner_address,
            &esdt_minter_wrapper,
            &rust_zero,
            |sc| {
                let token_identifier = managed_token_id!(PIGGY_TOKEN_IDENTIFIER);
                sc.esdt_identifier().set_token_id(token_identifier);
            },
        )
        .assert_ok();

    esdt_minter_wrapper
}

pub fn add_airdrop_amount<EsdtMinterObjBuilder>(
    blockchain_setup: &mut BlockchainSetup,
    esdt_minter_wrapper: &ContractObjWrapper<
        esdt_minter::ContractObj<DebugApi>,
        EsdtMinterObjBuilder,
    >,
    user_address: &Address,
    airdrop_amount: u64,
) -> TxResult
where
    EsdtMinterObjBuilder: 'static + Copy + Fn() -> esdt_minter::ContractObj<DebugApi>,
{
    blockchain_setup.blockchain_wrapper.execute_tx(
        &blockchain_setup.owner_address,
        &esdt_minter_wrapper,
        &rust_biguint!(0u64),
        |sc| {
            sc.add_airdrop_amount(
                ManagedAddress::from(user_address),
                managed_biguint!(airdrop_amount),
            );
        },
    )
}

pub fn add_interests_address<EsdtMinterObjBuilder>(
    blockchain_setup: &mut BlockchainSetup,
    esdt_minter_wrapper: &ContractObjWrapper<
        esdt_minter::ContractObj<DebugApi>,
        EsdtMinterObjBuilder,
    >,
    interests_address: &Address,
) -> TxResult
where
    EsdtMinterObjBuilder: 'static + Copy + Fn() -> esdt_minter::ContractObj<DebugApi>,
{
    blockchain_setup.blockchain_wrapper.execute_tx(
        &blockchain_setup.owner_address,
        &esdt_minter_wrapper,
        &rust_biguint!(0u64),
        |sc| {
            sc.add_interest_address(ManagedAddress::from(interests_address));
        },
    )
}

pub fn claim_airdrop<EsdtMinterObjBuilder>(
    blockchain_setup: &mut BlockchainSetup,
    esdt_minter_wrapper: &ContractObjWrapper<
        esdt_minter::ContractObj<DebugApi>,
        EsdtMinterObjBuilder,
    >,
    user_address: &Address,
) -> TxResult
where
    EsdtMinterObjBuilder: 'static + Copy + Fn() -> esdt_minter::ContractObj<DebugApi>,
{
    blockchain_setup.blockchain_wrapper.execute_tx(
        user_address,
        &esdt_minter_wrapper,
        &rust_biguint!(0u64),
        |sc| {
            sc.claim_airdrop();
        },
    )
}

pub fn claim_interests<EsdtMinterObjBuilder>(
    blockchain_setup: &mut BlockchainSetup,
    esdt_minter_wrapper: &ContractObjWrapper<
        esdt_minter::ContractObj<DebugApi>,
        EsdtMinterObjBuilder,
    >,
    user_address: &Address,
    amount: u64,
) -> TxResult
where
    EsdtMinterObjBuilder: 'static + Copy + Fn() -> esdt_minter::ContractObj<DebugApi>,
{
    blockchain_setup.blockchain_wrapper.execute_esdt_transfer(
        user_address,
        &esdt_minter_wrapper,
        PIGGY_TOKEN_IDENTIFIER,
        0u64,
        &rust_biguint!(amount),
        |sc| {
            sc.claim_interests();
        },
    )
}
