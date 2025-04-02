multiversx_sc::imports!();

/// Minimal proxy for the Jex pair contract
/// it will only be used to swap tokens
///
#[multiversx_sc::proxy]
pub trait JexPairProxy {
    #[payable("*")]
    #[endpoint(swapTokensFixedInput)]
    fn swap_tokens_fixed_input(&self, min_amount_out: BigUint);
}
