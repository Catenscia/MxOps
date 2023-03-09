elrond_wasm::imports!();
elrond_wasm::derive_imports!();

use elrond_wasm_debug::{
    managed_token_id, rust_biguint, testing_framework::ContractObjWrapper, tx_mock::TxResult,
    DebugApi,
};
use piggy_bank::PiggyBank;

use super::blockchain_mod::*;

pub fn setup_piggy_bank<PiggyBankObjBuilder>(
    sc_builder: PiggyBankObjBuilder,
    blockchain_setup: &mut BlockchainSetup,
    esdt_minter_address: Address,
) -> ContractObjWrapper<piggy_bank::ContractObj<DebugApi>, PiggyBankObjBuilder>
where
    PiggyBankObjBuilder: 'static + Copy + Fn() -> piggy_bank::ContractObj<DebugApi>,
{
    let blockchain_wrapper = &mut blockchain_setup.blockchain_wrapper;
    let rust_zero = rust_biguint!(0u64);

    let piggy_bank_wrapper = blockchain_wrapper.create_sc_account(
        &rust_zero,
        Some(&blockchain_setup.owner_address),
        sc_builder,
        ESDT_MINTER_WASM_PATH,
    );

    // deploy contract
    blockchain_wrapper
        .execute_tx(
            &blockchain_setup.owner_address,
            &piggy_bank_wrapper,
            &rust_zero,
            |sc| {
                let token_identifier = managed_token_id!(PIGGY_TOKEN_IDENTIFIER);
                sc.init(token_identifier, ManagedAddress::from(esdt_minter_address));
            },
        )
        .assert_ok();

    piggy_bank_wrapper
}

pub fn user_deposit<PiggyBankObjBuilder>(
    blockchain_setup: &mut BlockchainSetup,
    piggy_bank_wrapper: &ContractObjWrapper<piggy_bank::ContractObj<DebugApi>, PiggyBankObjBuilder>,
    user_address: &Address,
    amount: u64,
) -> TxResult
where
    PiggyBankObjBuilder: 'static + Copy + Fn() -> piggy_bank::ContractObj<DebugApi>,
{
    blockchain_setup.blockchain_wrapper.execute_esdt_transfer(
        user_address,
        &piggy_bank_wrapper,
        PIGGY_TOKEN_IDENTIFIER,
        0u64,
        &rust_biguint!(amount),
        |sc| {
            sc.deposit();
        },
    )
}

pub fn user_withdraw<PiggyBankObjBuilder>(
    blockchain_setup: &mut BlockchainSetup,
    piggy_bank_wrapper: &ContractObjWrapper<piggy_bank::ContractObj<DebugApi>, PiggyBankObjBuilder>,
    user_address: &Address
) -> TxResult
where
    PiggyBankObjBuilder: 'static + Copy + Fn() -> piggy_bank::ContractObj<DebugApi>,
{
    blockchain_setup.blockchain_wrapper.execute_tx(
        user_address,
        &piggy_bank_wrapper,
        &rust_biguint!(0),
        |sc| {
            sc.withdraw();
        },
    )
}