elrond_wasm::imports!();
elrond_wasm::derive_imports!();

use elrond_wasm::types::Address;
use elrond_wasm_debug::{rust_biguint, testing_framework::BlockchainStateWrapper};

pub const ESDT_MINTER_WASM_PATH: &'static str = "output/esdt-minter.wasm";
pub const PIGGY_BANK_WASM_PATH: &'static str = "output/piggy-bank.wasm";

pub const PIGGY_TOKEN_IDENTIFIER: &[u8] = b"PIGGY-cc4852";
pub const META_ESDT_NAME: &[u8] = b"Piggy Bank Token";

pub const ESDT_MINTER_INTEREST_PERCENTAGE: u64 = 100; //100%

pub struct BlockchainSetup {
    pub blockchain_wrapper: BlockchainStateWrapper,
    pub owner_address: Address,
    pub user_address: Address,
}

pub fn create_blockchain_wrapper() -> BlockchainSetup {
    let rust_zero = rust_biguint!(0u64);
    let mut blockchain_wrapper = BlockchainStateWrapper::new();
    let owner_address = blockchain_wrapper.create_user_account(&rust_zero);
    let user_address = blockchain_wrapper.create_user_account(&rust_zero);

    BlockchainSetup {
        blockchain_wrapper,
        owner_address,
        user_address
    }
}
