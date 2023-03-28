multiversx_sc::imports!();

/// Proxy for the esdt-minter contract
/// This proxy will be used only to claim interest on the piggy token
///
#[multiversx_sc::proxy]
pub trait EsdtMinterProxy {
    #[payable("*")]
    #[endpoint(claimInterests)]
    fn claim_interests(&self) -> EsdtTokenPayment<Self::Api>;
}
