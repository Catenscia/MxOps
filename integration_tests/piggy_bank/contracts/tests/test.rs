multiversx_sc::imports!();
multiversx_sc::derive_imports!();

use multiversx_sc_scenario::{rust_biguint, DebugApi};

pub mod common;
use crate::common::{blockchain_mod::*, setup_contracts};
use common::{esdt_minter_mod::*, piggy_bank_mod::*};

#[test]
fn test_correct_airdrop_claim() {
    let _ = DebugApi::dummy();

    let mut blockchain_setup = create_blockchain_wrapper();
    let (esdt_minter_wrapper, _) = setup_contracts(
        &mut blockchain_setup,
        esdt_minter::contract_obj,
        piggy_bank::contract_obj,
    );

    // add some token amount to the user and make him claim
    let airdrop_user = blockchain_setup.user_address.clone();
    add_airdrop_amount(
        &mut blockchain_setup,
        &esdt_minter_wrapper,
        &airdrop_user,
        150_000,
    )
    .assert_ok();
    claim_airdrop(&mut blockchain_setup, &esdt_minter_wrapper, &airdrop_user).assert_ok();

    // check that the airdrop was sent correctly
    blockchain_setup.blockchain_wrapper.check_esdt_balance(
        &airdrop_user,
        PIGGY_TOKEN_IDENTIFIER,
        &rust_biguint!(150_000),
    );
}

#[test]
fn test_interests_whitelist() {
    let _ = DebugApi::dummy();

    let mut blockchain_setup = create_blockchain_wrapper();
    let esdt_minter_wrapper = setup_esdt_minter(esdt_minter::contract_obj, &mut blockchain_setup);

    let interest_user = blockchain_setup.user_address.clone();

    // add some token amount to the user and make him claim (necessary to avoid esdt transfer error)
    add_airdrop_amount(
        &mut blockchain_setup,
        &esdt_minter_wrapper,
        &interest_user,
        150_000,
    )
    .assert_ok();
    claim_airdrop(&mut blockchain_setup, &esdt_minter_wrapper, &interest_user).assert_ok();

    // assert user can not claim interests
    claim_interests(
        &mut blockchain_setup,
        &esdt_minter_wrapper,
        &interest_user,
        0,
    )
    .assert_user_error("Item not whitelisted");

    // add user to the interest whitelist
    add_interests_address(&mut blockchain_setup, &esdt_minter_wrapper, &interest_user).assert_ok();

    // assert user can claim interests
    claim_interests(
        &mut blockchain_setup,
        &esdt_minter_wrapper,
        &interest_user,
        0,
    )
    .assert_ok();
}

#[test]
fn test_piggy_cycle() {
    let _ = DebugApi::dummy();

    let mut blockchain_setup = create_blockchain_wrapper();
    let (esdt_minter_wrapper, piggy_bank_wrapper) = setup_contracts(
        &mut blockchain_setup,
        esdt_minter::contract_obj,
        piggy_bank::contract_obj,
    );

    // add some token amount to the user and make him claim
    let airdrop_user = blockchain_setup.user_address.clone();
    add_airdrop_amount(
        &mut blockchain_setup,
        &esdt_minter_wrapper,
        &airdrop_user,
        150_000,
    )
    .assert_ok();
    claim_airdrop(&mut blockchain_setup, &esdt_minter_wrapper, &airdrop_user).assert_ok();

    // make the user deposit into the piggy bank
    user_deposit(
        &mut blockchain_setup,
        &piggy_bank_wrapper,
        &airdrop_user,
        150_000,
    )
    .assert_ok();

    // assert user has no fund left
    blockchain_setup.blockchain_wrapper.check_esdt_balance(
        &airdrop_user,
        PIGGY_TOKEN_IDENTIFIER,
        &rust_biguint!(0),
    );

    // make the user withdraw from the piggy bank
    user_withdraw(&mut blockchain_setup, &piggy_bank_wrapper, &airdrop_user).assert_ok();

    // assert user has twice as much tokens as at the beginning
    blockchain_setup.blockchain_wrapper.check_esdt_balance(
        &airdrop_user,
        PIGGY_TOKEN_IDENTIFIER,
        &rust_biguint!(300_000),
    );
}
