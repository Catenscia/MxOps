#![no_std]

elrond_wasm::imports!();
elrond_wasm::derive_imports!();

#[elrond_wasm::contract]
pub trait EsdtMinter {
    // #################   storage    #################

    /// Token that will be issued and minted by the contract
    #[view(getEsdtIdentifier)]
    #[storage_mapper("esdt_identifier")]
    fn esdt_identifier(&self) -> FungibleTokenMapper<Self::Api>;

    /// Airdop amount available per address
    #[view(getAirdropAmount)]
    #[storage_mapper("airdop_amount")]
    fn airdrop_amount(&self, address: ManagedAddress) -> SingleValueMapper<BigUint>;

    // #################   views    #################

    // #################   init    #################
    #[init]
    fn init(&self) {}

    // #################   endpoints    #################

    /// Claim the airdrop amount assigned to the caller
    /// 
    /// ### Return Payments:
    ///
    /// * **airdrop_payment**: airdrop for the user
    ///
    #[endpoint(claimAirdrop)]
    fn claim_airdrop(&self) {
        let caller = self.blockchain().get_caller();
        let claimable_amount = self.airdrop_amount(caller.clone()).get();
        self.esdt_identifier().mint_and_send(&caller, claimable_amount);
        self.airdrop_amount(caller).clear();
    }

    // #################   restricted endpoints    #################

    /// OWNER RESTRICTED
    ///
    /// Issue and set all roles for the token of the contract
    ///
    /// ### Arguments
    ///
    /// * **token_display_name** - `ManagedBuffer` Display name for the LP token
    /// * **token_ticker** - `ManagedBuffer` Ticker to designate the LP token
    /// * **num_decimals** - `usize` Number of decimals for the LP token
    ///
    /// ### Payments:
    ///
    /// * **registering_payment**: Egld amount to exactly cover the registering cost of the token.
    ///
    #[only_owner]
    #[endpoint(issueToken)]
    fn issue_token(
        &self,
        token_display_name: ManagedBuffer,
        token_ticker: ManagedBuffer,
        num_decimals: usize,
    ) {
        let register_cost = self.call_value().egld_value();
        self.esdt_identifier().issue_and_set_all_roles(
            register_cost,
            token_display_name,
            token_ticker,
            num_decimals,
            None,
        );
    }

    /// OWNER RESTRICTED
    ///
    /// Add some amount to a user airdrop balance
    ///
    /// ### Arguments
    ///
    /// * **address** - `Address` Address of the user that will ave its amount augmented
    /// * **amount** - `BigUint` Amount of token to mint and send
    ///
    #[only_owner]
    #[endpoint(addAirdropAmount)]
    fn add_airdrop_amount(&self, address: ManagedAddress, amount: BigUint) {
        self.airdrop_amount(address).update(|val| *val += amount);
    }
}
