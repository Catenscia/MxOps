#![no_std]

multiversx_sc::imports!();
multiversx_sc::derive_imports!();

#[multiversx_sc::contract]
pub trait EsdtMinter:
    multiversx_sc_modules::default_issue_callbacks::DefaultIssueCallbacksModule
{
    // #################   storage    #################

    /// Token that will be issued and minted by the contract
    #[view(getEsdtIdentifier)]
    #[storage_mapper("esdt_identifier")]
    fn esdt_identifier(&self) -> FungibleTokenMapper<Self::Api>;

    /// Airdop amount available per address
    #[view(getAirdropAmount)]
    #[storage_mapper("airdop_amount")]
    fn airdrop_amount(&self, address: ManagedAddress) -> SingleValueMapper<BigUint>;

    /// Percentage of token to distribute when interests are claimed
    /// Ex: 12 -> 12%
    #[view(getInterestPercentage)]
    #[storage_mapper("interest_percentage")]
    fn interest_percentage(&self) -> SingleValueMapper<u64>;

    /// Whitelist containing the addresses allowed to call the interests endpoint
    ///
    #[storage_mapper("interest_whitelist")]
    fn interest_whitelist(&self) -> WhitelistMapper<Self::Api, ManagedAddress>;

    // #################   views    #################

    // #################   init && upgrade    #################
    #[init]
    fn init(&self, interest_percentage: u64) {
        self.interest_percentage().set(interest_percentage);
    }

    #[upgrade]
    fn upgrade(&self) {}

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
        require!(&claimable_amount > &BigUint::zero(), "Nothing to claim");
        self.esdt_identifier()
            .mint_and_send(&caller, claimable_amount);
        self.airdrop_amount(caller).clear();
    }

    // #################   restricted endpoints    #################

    /// INTEREST WHITELIST RESTRICTED
    ///
    /// Receive a token payment and send it back with interests.
    ///
    /// ### Payments:
    ///
    /// * **capital_payment**: payment in the token of the contract.
    ///
    /// ### Return Payments:
    ///
    /// * **payment_with_interests**: payment composed of the received capital and the interests
    ///
    #[payable("*")]
    #[endpoint(claimInterests)]
    fn claim_interests(&self) -> EsdtTokenPayment<Self::Api> {
        let capital_payment = self.call_value().single_esdt();

        // check that the call is allowed and correct
        let caller = self.blockchain().get_caller();
        self.interest_whitelist().require_whitelisted(&caller);
        self.require_good_token_identifier(&capital_payment);

        // mint the interests
        let interest_amount = &capital_payment.amount * self.interest_percentage().get() / 100u64;
        self.esdt_identifier().mint(interest_amount.clone());

        // send back the capital along the the interests
        let payment_with_interests = EsdtTokenPayment::new(
            capital_payment.token_identifier,
            0u64,
            capital_payment.amount + interest_amount,
        );

        self.send().direct_esdt(
            &caller,
            &payment_with_interests.token_identifier,
            0u64,
            &payment_with_interests.amount,
        );

        payment_with_interests
    }

    /// OWNER RESTRICTED
    ///
    /// Add an address to the interest whitelist
    ///
    /// ### Arguments
    ///
    /// * **address** - `ManagedAddress` Adress to add to the interest whitelist
    ///
    #[only_owner]
    #[endpoint(addInterestAddress)]
    fn add_interest_address(&self, address: ManagedAddress) {
        self.interest_whitelist().add(&address);
    }

    /// OWNER RESTRICTED
    ///
    /// Remove an address from the interest whitelist
    ///
    /// ### Arguments
    ///
    /// * **address** - `ManagedAddress` Adress to remove from the interest whitelist
    ///
    #[only_owner]
    #[endpoint(removeInterestAddress)]
    fn remove_interest_address(&self, address: ManagedAddress) {
        self.interest_whitelist().remove(&address);
    }

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
    #[payable("EGLD")]
    #[only_owner]
    #[endpoint(issueToken)]
    fn issue_token(
        &self,
        token_display_name: ManagedBuffer,
        token_ticker: ManagedBuffer,
        num_decimals: usize,
    ) {
        let register_cost = &*self.call_value().egld_value();
        self.esdt_identifier().issue_and_set_all_roles(
            register_cost.clone(),
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

    // #################   functions    #################

    /// Require a payment to be made of the piggy token
    /// by checking its token identifier.
    ///
    /// ### Arguments
    ///
    /// * **payment** - `&EsdtTokenPayment` payment to check
    ///
    fn require_good_token_identifier(&self, payment: &EsdtTokenPayment) {
        require!(
            payment.token_identifier == self.esdt_identifier().get_token_id(),
            "Token identifier do not match the esdt token"
        );
    }
}
