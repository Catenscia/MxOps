#![no_std]

mod jex_pair_proxy;

#[allow(unused_imports)]
use multiversx_sc::imports::*;

/// This contract acts as trader on the JEX/WEGLD pair from Jexchange
/// A specified user (bot) will be able to trigger market buy or market sell for JEX
#[multiversx_sc::contract]
pub trait TraderSc {
    // #################################
    //             storages
    // #################################

    /// Holds the identifier of the JEX token used when trading
    ///
    #[view(getJexIdentifier)]
    #[storage_mapper("jex_identifier")]
    fn jex_identifier(&self) -> SingleValueMapper<TokenIdentifier>;

    /// Holds the identifier of the WEGLD token used when trading
    ///
    #[view(getWegldIdentifier)]
    #[storage_mapper("wegld_identifier")]
    fn wegld_identifier(&self) -> SingleValueMapper<TokenIdentifier>;

    /// Holds the address of the jex pair contract
    ///
    #[view(getJexPairAddress)]
    #[storage_mapper("jex_pair_address")]
    fn jex_pair_address(&self) -> SingleValueMapper<ManagedAddress>;

    /// Holds the address of the only account allowed to trigger trades
    /// besides the owner
    ///
    #[view(getExecutorAddress)]
    #[storage_mapper("executor_address")]
    fn executor_address(&self) -> SingleValueMapper<ManagedAddress>;

    /// Initialize the contract with all the storage values
    #[init]
    fn init(
        &self,
        jex_identifier: TokenIdentifier,
        wegld_identifier: TokenIdentifier,
        jex_pair_address: ManagedAddress,
        executor_address: ManagedAddress,
    ) {
        self.jex_identifier().set(jex_identifier);
        self.wegld_identifier().set(wegld_identifier);
        self.jex_pair_address().set(jex_pair_address);
        self.executor_address().set(executor_address);
    }

    /// nothing to do on upgrade
    ///
    #[upgrade]
    fn upgrade(&self) {}

    // #################################
    //         public endpoints
    // #################################

    /// Callable by anyone, serves only as a way to
    /// send funds to the contract
    #[payable("*")]
    #[endpoint]
    fn deposit(&self) {}

    // #################################
    //       restricted endpoints
    // #################################

    /// EXECUTOR RESTRICTED
    /// Execute a market order (no minimum output) on the JEX/WEGLD pair
    ///
    /// ### Arguments
    ///
    /// * **is_buy** - `bool`: if the contract must buy JEX tokens. Otherwise it will sell JEX tokens
    /// * **input_amount** - `BigUint`: amount of input token to send
    ///
    /// ### Returns
    ///
    /// * `BigUint`: amount of output tokens received
    ///
    #[endpoint(executeTrade)]
    fn execute_trade(&self, is_buy: bool, input_amount: BigUint) -> BigUint {
        // check caller rights
        let caller = self.blockchain().get_caller();
        require!(
            caller == self.executor_address().get()
                || caller == self.blockchain().get_owner_address(),
            "Forbidden"
        );

        // figure out which token to send
        let input_identifier = if is_buy {
            self.wegld_identifier().get()
        } else {
            self.jex_identifier().get()
        };

        // swap
        let back_transfers = self
            .jex_pair_proxy(self.jex_pair_address().get())
            .swap_tokens_fixed_input(BigUint::zero())
            .single_esdt(&input_identifier, 0u64, &input_amount)
            .returns(ReturnsBackTransfers)
            .sync_call();

        // extract quantity of tokens received
        require!(
            back_transfers.esdt_payments.len() == 1,
            "Expect to receive 1 back transfer"
        );
        back_transfers.esdt_payments.get(0).amount
    }

    // #################################
    //          owner endpoints
    // #################################

    /// OWNER RESTRICTED
    /// Allow the owner to withdraw some esdt tokens from the contract
    ///
    /// ### Arguments
    ///
    /// * **payment** - `EsdtTokenPayment`: tokens that the contract should send to the owner
    ///
    #[only_owner]
    #[endpoint]
    fn withdraw(&self, payment: EsdtTokenPayment) {
        self.send()
            .direct_non_zero_esdt_payment(&self.blockchain().get_owner_address(), &payment);
    }

    // #################################
    //          owner endpoints
    // #################################
    #[proxy]
    fn jex_pair_proxy(&self, sc_address: ManagedAddress) -> jex_pair_proxy::Proxy<Self::Api>;
}
