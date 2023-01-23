#![no_std]

mod esdt_minter_proxy;

elrond_wasm::imports!();

#[elrond_wasm::contract]
pub trait PiggyBank {
    // #################   proxy    #################

    #[proxy]
    fn esdt_minter_proxy(&self, sc_address: ManagedAddress) -> esdt_minter_proxy::Proxy<Self::Api>;

    // #################   storage    #################

    /// Token identifier for the token of the bank
    #[view(getTokenIdentifier)]
    #[storage_mapper("piggy_token_identifier")]
    fn piggy_token_identifier(&self) -> SingleValueMapper<TokenIdentifier>;

    /// Address of the esdt-minter contract for the piggy token
    #[view(getEsdtMinnterAddress)]
    #[storage_mapper("esdt_minter_address")]
    fn esdt_minter_address(&self) -> SingleValueMapper<ManagedAddress>;

    /// Amount of token deposit per adress
    #[view(getAddressAmount)]
    #[storage_mapper("address_amount")]
    fn address_amount(&self, address: ManagedAddress) -> SingleValueMapper<BigUint>;

    // #################   views    #################

    // #################   init    #################
    #[init]
    fn init(&self, piggy_token_identifier: TokenIdentifier, esdt_minter_address: ManagedAddress) {
        self.piggy_token_identifier()
            .set_if_empty(piggy_token_identifier);
        self.esdt_minter_address().set_if_empty(esdt_minter_address);
    }

    // #################   endpoints    #################

    /// Allow a user to deposit some piggy tokens in the piggy bank.
    ///
    /// ### Payments
    ///
    /// * **deposit_payment** : Single payment of piggy token
    ///
    #[endpoint(deposit)]
    #[payable("*")]
    fn deposit(&self) {
        let deposit_payment = self.call_value().single_esdt();
        let caller = self.blockchain().get_caller();
        self.require_good_token_identifier(&deposit_payment);
        self.address_amount(caller)
            .update(|val| *val += deposit_payment.amount);
    }

    /// Allow a user to withdraw all its piggy tokens from the piggy bank.
    /// Interest will be issued and send along the principal.
    ///
    /// ### Return Payments
    ///
    /// * **withdraw_payment** : Single payment of piggy tokens containing all the user deposits and the interests earned
    ///
    #[endpoint(withdraw)]
    #[payable("*")]
    fn withdraw(&self) {
        let caller = self.blockchain().get_caller();
        let available_amount = self.address_amount(caller.clone()).get();
        require!(&available_amount > &BigUint::zero(), "Nothing to withdraw");

        let payment_with_interests = self.call_claim_interests_sync(available_amount);

        // send the deposit with the interests back to the caller
        self.send().direct_esdt(
            &caller,
            &payment_with_interests.token_identifier,
            payment_with_interests.token_nonce,
            &payment_with_interests.amount,
        );

        // clear the deposit amount of the caller
        self.address_amount(caller).clear();
    }

    // #################   restricted endpoints    #################

    // #################   functions    #################

    /// Sync call to the esdt-minter contract of the piggy token to claim the interests on some tokens
    ///
    /// ### Arguments
    ///
    /// * **amount** - `BigUint` Amount of token to send for interest requests
    ///
    /// ### Returns
    ///
    /// * **payment** - `EsdtTokenPayment<Self::Api>` back payment recieved from the esdt-minter (principal + interests)
    ///
    fn call_claim_interests_sync(&self, amount: BigUint) -> EsdtTokenPayment<Self::Api> {
        let proxy_address = self.esdt_minter_address().get();
        let mut proxy_instance = self.esdt_minter_proxy(proxy_address);

        proxy_instance
            .claim_interests()
            .with_esdt_transfer((self.piggy_token_identifier().get(), 0u64, amount))
            .execute_on_dest_context()
    }

    /// Require a payment to be made of the piggy token
    /// by checking its token identifier.
    ///
    /// ### Arguments
    ///
    /// * **payment** - `&EsdtTokenPayment` payment to check
    ///
    fn require_good_token_identifier(&self, payment: &EsdtTokenPayment) {
        require!(
            payment.token_identifier == self.piggy_token_identifier().get(),
            "Token identifier do not match the piggy token"
        );
    }
}
