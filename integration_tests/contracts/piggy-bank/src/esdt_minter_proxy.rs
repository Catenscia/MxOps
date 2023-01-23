elrond_wasm::imports!();

/// Proxy for the esdt-minter contract
/// This proxy will be used only to claim interest on the piggy token
///
#[elrond_wasm::proxy]
pub trait EsdtMinterProxy {
    #[payable("*")]
    #[endpoint(claimInterests)]
    fn claim_interests(&self) -> EsdtTokenPayment<Self::Api>;
}
