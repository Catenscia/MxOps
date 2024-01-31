#![no_std]

use multiversx_sc::hex_literal::hex;

multiversx_sc::imports!();
multiversx_sc::derive_imports!();

pub const TOKEN_IDENTIFIER: &[u8] = b"WEGLD-abcdef";
pub const TOKEN_IDENTIFIER_2: &[u8] = b"MEX-abcdef";
pub const HEX_ADDRESS: [u8; 32] =
    hex!("000000000000000005004d4e468a6785c67dcf63611a05266562ba913638aa59");
/// erd1qqqqqqqqqqqqqpgqf48ydzn8shr8mnmrvydq2fn9v2afzd3c4fvsk4wglm

#[derive(TopEncode, TopDecode, NestedEncode, NestedDecode, TypeAbi, PartialEq, Eq)]
pub struct MyStruct<M: ManagedTypeApi> {
    pub int: u16,
    pub seq: ManagedVec<M, u8>,
    pub another_byte: u8,
    pub uint_32: u32,
    pub uint_64: u64,
}

#[derive(TopEncode, TopDecode, NestedEncode, NestedDecode, TypeAbi, PartialEq, Eq)]
pub struct Struct<M: ManagedTypeApi> {
    pub int: u16,
    pub seq: ManagedVec<M, u8>,
    pub another_byte: u8,
    pub uint_32: u32,
    pub uint_64: u64,
}

#[derive(TopEncode, TopDecode, NestedEncode, NestedDecode, TypeAbi, PartialEq, Eq)]
pub enum DayOfWeek {
    Monday,
    Tuesday,
    Wednesday,
    Thursday,
    Friday,
    Saturday,
    Sunday,
}

#[derive(TopEncode, TopDecode, NestedEncode, NestedDecode, TypeAbi, PartialEq, Eq)]
pub enum EnumWithEverything<M: ManagedTypeApi> {
    Default,
    Today(DayOfWeek),
    Write(ManagedVec<M, u8>, u16),
    Struct {
        int: u16,
        seq: ManagedVec<M, u8>,
        another_byte: u8,
        uint_32: u32,
        uint_64: u64,
    },
}

/// Although it is considered a bad practice, in this contract each endpoint will be defined
/// aside the associated views when needed to ease the writing and reading of tests
#[multiversx_sc::contract]
pub trait DataStore {
    // #################   storage    #################

    #[view]
    #[storage_mapper("my_usize")]
    fn my_usize(&self) -> SingleValueMapper<usize>;

    #[view]
    #[storage_mapper("my_u8")]
    fn my_u8(&self) -> SingleValueMapper<u8>;

    #[view]
    #[storage_mapper("my_u16")]
    fn my_u16(&self) -> SingleValueMapper<u16>;

    #[view]
    #[storage_mapper("my_u32")]
    fn my_u32(&self) -> SingleValueMapper<u32>;

    #[view]
    #[storage_mapper("my_u64")]
    fn my_u64(&self) -> SingleValueMapper<u64>;

    #[view]
    #[storage_mapper("my_isize")]
    fn my_isize(&self) -> SingleValueMapper<isize>;

    #[view]
    #[storage_mapper("my_i8")]
    fn my_i8(&self) -> SingleValueMapper<i8>;

    #[view]
    #[storage_mapper("my_i16")]
    fn my_i16(&self) -> SingleValueMapper<i16>;

    #[view]
    #[storage_mapper("my_i32")]
    fn my_i32(&self) -> SingleValueMapper<i32>;

    #[view]
    #[storage_mapper("my_i64")]
    fn my_i64(&self) -> SingleValueMapper<i64>;

    #[view]
    #[storage_mapper("my_token_identifier")]
    fn my_token_identifier(&self) -> SingleValueMapper<TokenIdentifier>;

    #[view]
    #[storage_mapper("my_managed_address")]
    fn my_managed_address(&self) -> SingleValueMapper<ManagedAddress>;

    #[view]
    #[storage_mapper("my_biguint")]
    fn my_biguint(&self) -> SingleValueMapper<BigUint>;

    #[view]
    #[storage_mapper("my_bigint")]
    fn my_bigint(&self) -> SingleValueMapper<BigInt>;

    #[view]
    #[storage_mapper("my_option_biguint")]
    fn my_option_biguint(&self) -> SingleValueMapper<Option<BigUint>>;

    #[view]
    #[storage_mapper("my_vec_biguint")]
    fn my_vec_biguint(&self) -> VecMapper<BigUint>;

    #[view]
    #[storage_mapper("my_enum_with_everything")]
    fn my_enum_with_everything(&self) -> SingleValueMapper<EnumWithEverything<Self::Api>>;

    // #################   stand-alone views    #################

    #[view]
    fn view_optional_1(&self, my_optional: OptionalValue<bool>) -> OptionalValue<bool> {
        require!(
            my_optional.clone().into_option().unwrap() == true,
            "my_optional failed"
        );
        my_optional
    }

    // #################   init && upgrade    #################

    #[init]
    fn init(&self, my_enum: EnumWithEverything<Self::Api>, my_u32: u32, my_i8: i8) {
        require!(my_enum == EnumWithEverything::Default, "my_enum failed");
        self.my_enum_with_everything().set(my_enum);

        require!(my_u32 == 123455, "my_u32 failed");
        self.my_u32().set(my_u32);

        require!(my_i8 == -3, "my_i8 failed");
        self.my_i8().set(my_i8);
    }

    #[view]
    fn get_init_params(&self) -> MultiValue3<EnumWithEverything<Self::Api>, u32, i8> {
        (
            self.my_enum_with_everything().get(),
            self.my_u32().get(),
            self.my_i8().get(),
        )
            .into()
    }

    #[upgrade]
    fn upgrade(&self, my_biguint: BigUint, my_bigint: BigInt) {
        require!(
            my_biguint == BigUint::from(10u64).pow(18),
            "my_biguint failed"
        );
        self.my_biguint().set(my_biguint);

        require!(
            my_bigint == BigInt::from(-10i64).pow(17),
            "my_bigint failed"
        );
        self.my_bigint().set(my_bigint);
    }

    #[view]
    fn get_upgrade_params(&self) -> (BigUint<Self::Api>, BigInt<Self::Api>) {
        (self.my_biguint().get(), self.my_bigint().get())
    }

    // #################   endpoints && their views    #################

    #[endpoint]
    fn test_1(
        &self,
        my_option_biguint: Option<BigUint>,
        my_optional_token_identifier: OptionalValue<TokenIdentifier>,
    ) {
        require!(
            my_option_biguint.clone().unwrap() == BigUint::from(123987u64),
            "my_option_biguint failed"
        );
        self.my_option_biguint().set(my_option_biguint);

        require!(
            my_optional_token_identifier.is_none() == true,
            "my_optional_token_identifier failed"
        );
        self.my_token_identifier().clear();
    } // no views, check directly the mappers

    #[endpoint]
    fn test_2(
        &self,
        my_managed_address: ManagedAddress,
        my_optional_token_identifier: OptionalValue<TokenIdentifier>,
    ) {
        require!(
            my_managed_address == ManagedAddress::from(HEX_ADDRESS),
            "my_option_biguint failed"
        );
        self.my_managed_address().set(my_managed_address);

        require!(
            my_optional_token_identifier.is_none() == false,
            "my_optional_token_identifier failed"
        );
        let my_token_identifier = my_optional_token_identifier.into_option().unwrap();
        require!(
            my_token_identifier.clone() == TokenIdentifier::from(TOKEN_IDENTIFIER),
            "my_token_identifier failed"
        );
        self.my_token_identifier().set(my_token_identifier);
    }

    #[view]
    fn get_test_2_params(&self) -> (ManagedAddress<Self::Api>, TokenIdentifier) {
        (
            self.my_managed_address().get(),
            self.my_token_identifier().get(),
        )
    }

    #[endpoint]
    fn test_3(&self, my_isize: isize, biguints: MultiValueEncoded<BigUint>) {
        self.my_vec_biguint().clear();
        for (index, ref_value) in biguints.to_vec().iter().enumerate() {
            let value = (*ref_value).clone();
            require!(value == BigUint::from(index), "biguints_vec failed");
            self.my_vec_biguint().push(&value);
        }

        require!(my_isize == -3isize, "my_isize failed");
        self.my_isize().set(my_isize);
    }

    #[view]
    fn get_test_3_params(&self) -> MultiValue2<isize, MultiValueEncoded<BigUint>> {
        let my_biguints_as_multi_values =
            MultiValueEncoded::from_iter(self.my_vec_biguint().iter());
        (self.my_isize().get(), my_biguints_as_multi_values).into()
    }

    #[endpoint]
    fn test_4(&self, biguints: ManagedVec<BigUint>) {
        self.my_vec_biguint().clear();
        for (index, ref_value) in biguints.iter().enumerate() {
            let value = (*ref_value).clone();
            require!(value == BigUint::from(index), "biguints_vec failed");
            self.my_vec_biguint().push(&value);
        }
    }

    #[view]
    fn get_test_4_params(&self) -> ManagedVec<BigUint> {
        let mut managed_vec = ManagedVec::new();
        for element in self.my_vec_biguint().iter() {
            managed_vec.push(element);
        }
        managed_vec
    }

    // #################   pure views    #################

    #[view]
    fn view_test_1(
        &self,
        a: DayOfWeek,
        b: DayOfWeek,
        c: EnumWithEverything<Self::Api>,
        d: EnumWithEverything<Self::Api>,
        e: EnumWithEverything<Self::Api>,
        f: EnumWithEverything<Self::Api>,
    ) -> MultiValue6<
        DayOfWeek,
        DayOfWeek,
        EnumWithEverything<Self::Api>,
        EnumWithEverything<Self::Api>,
        EnumWithEverything<Self::Api>,
        EnumWithEverything<Self::Api>,
    > {
        require!(a == DayOfWeek::Monday, "a failed");
        require!(b == DayOfWeek::Sunday, "b failed");
        require!(c == EnumWithEverything::Default, "c failed");
        require!(
            d == EnumWithEverything::Today(DayOfWeek::Tuesday),
            "d failed"
        );
        let mut expected_e_seq = ManagedVec::new();
        expected_e_seq.push(1u8);
        expected_e_seq.push(2u8);
        expected_e_seq.push(4u8);
        expected_e_seq.push(8u8);
        require!(
            e == EnumWithEverything::Write(expected_e_seq, 14u16),
            "e failed"
        );
        let mut expected_f_seq = ManagedVec::new();
        expected_f_seq.push(9u8);
        expected_f_seq.push(45u8);
        require!(
            f == EnumWithEverything::Struct {
                int: 8u16,
                seq: expected_f_seq,
                another_byte: 0u8,
                uint_32: 789484u32,
                uint_64: 485u64
            },
            "f failed"
        );
        (a, b, c, d, e, f).into()
    }

    #[view]
    fn view_test_2(
        &self,
        payments: MultiValueEncoded<EsdtTokenPayment>,
    ) -> MultiValueEncoded<EsdtTokenPayment> {
        let payment_vec = payments.to_vec();
        require!(payments.len() == 2, "Wrong payments number");
        require!(
            payment_vec.get(0)
                == EsdtTokenPayment::new(
                    TokenIdentifier::from(TOKEN_IDENTIFIER),
                    0,
                    BigUint::from(89784651u64)
                ),
            "Wrong first payment"
        );
        require!(
            payment_vec.get(1)
                == EsdtTokenPayment::new(
                    TokenIdentifier::from(TOKEN_IDENTIFIER_2),
                    0,
                    BigUint::from(184791484u64)
                ),
            "Wrong second payment"
        );
        payments
    }
}
