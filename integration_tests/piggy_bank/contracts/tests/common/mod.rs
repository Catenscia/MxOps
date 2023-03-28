use multiversx_sc_scenario::{rust_biguint, testing_framework::ContractObjWrapper, DebugApi};
use esdt_minter::EsdtMinter;

multiversx_sc::imports!();
multiversx_sc::derive_imports!();

pub mod blockchain_mod;
pub mod esdt_minter_mod;
pub mod piggy_bank_mod;

pub fn setup_contracts<EsdtMinterObjBuilder, PiggyBankObjBuilder>(
    blockchain_setup: &mut blockchain_mod::BlockchainSetup,
    esdt_minter_builder: EsdtMinterObjBuilder,
    piggy_bank_builder: PiggyBankObjBuilder,
) -> (
    ContractObjWrapper<esdt_minter::ContractObj<DebugApi>, EsdtMinterObjBuilder>,
    ContractObjWrapper<piggy_bank::ContractObj<DebugApi>, PiggyBankObjBuilder>,
)
where
    EsdtMinterObjBuilder: 'static + Copy + Fn() -> esdt_minter::ContractObj<DebugApi>,
    PiggyBankObjBuilder: 'static + Copy + Fn() -> piggy_bank::ContractObj<DebugApi>,
{
    let esdt_minter_wrapper =
        esdt_minter_mod::setup_esdt_minter(esdt_minter_builder, blockchain_setup);
    let piggy_bank_wrapper = piggy_bank_mod::setup_piggy_bank(
        piggy_bank_builder,
        blockchain_setup,
        esdt_minter_wrapper.address_ref().clone(),
    );

    // set piggy bank address in the esdt-minter

    blockchain_setup
        .blockchain_wrapper
        .execute_tx(
            &blockchain_setup.owner_address,
            &esdt_minter_wrapper,
            &rust_biguint!(0u64),
            |sc| {
                sc.add_interest_address(ManagedAddress::from(piggy_bank_wrapper.address_ref()));
            },
        )
        .assert_ok();

    (esdt_minter_wrapper, piggy_bank_wrapper)
}
