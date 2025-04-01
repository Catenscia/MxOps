# Serialization

When interacting with the blockchain, a very important aspect to keep in mind is the data format, in particular when dealing with smart-contracts and when the data has a complex representation such as custom structures with nested elements. To make things easy for the user, MxOps will use ABI definitions to:
- automatically convert the data provided by the user into the format expected by the blockchain
- automatically parse the data received from the blockchain into a human usable format

The rest of this section details how the user should provide data and use data when interacting with a smart-contract.

## Monotypes

Most monotypes can be directly provided as-is, this includes: `bool`, `u<n>`, `i<n>`, `BigUint`, `BigInt`, `TokenIdentifier`, `EgldOrEsdtTokenIdentifier` and `utf-8 string`.

Example:

```yaml
- type: ContractQuery
  contract: my_contract
  endpoint: my_query_endpoint
  arguments:
    - true  # bool
    - 2  # u8
    - -623  # i32
    - 1329809823980832  # BigUint
    - -9248872872987083940  # BigInt
    - WEGLD-abcdef  # TokenIdentifier
    - WEGLD-abcdef  # EgldOrEsdtTokenIdentifier
    - "my super utf8 string"  # utf-8 string
```

## Bytes

`bytes` are trickier as yaml don't support directly the bytes type. If your intention is to provided vector, list of elements, string or anything that should be converted to bytes, then you can write them in the original format and MxOps will convert them for you.

However, if you really need to pass pure bytes data, then you must use one of the following syntax:   

- `bytes:<b64_encoded_data>`, where `b64_encoded_data` is your bytes data in the b64 format.
- `"<hex_encoded_data>"`, where `hex_encoded_data` is your bytes data in the hex format, prodided as a string.


```yaml
- type: ContractQuery
  contract: my_contract
  endpoint: my_query_endpoint
  arguments:
    - [1, 2, 4, 8]  # vec that will be converted to bytes
    - "bytes:AQIECA=="  # same bytes data but in the b64 format
    - "0x01020408"  # same bytes data but in the hex format, the quotes are mandatory!
```

## Address

Addresses are passed in their bech32 form.

```yaml
- type: ContractQuery
  contract: my_contract
  endpoint: my_query_endpoint
  arguments:
    - erd1qqqqqqqqqqqqqqqpqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqplllst77y4l  # address
```

## List, Tuple, Vec, ManagedVec

`Lists`, `Tuples`, `Vecs`, `ManagedVecs` can be specified as list using yaml syntax or direct list format:

```yaml
- type: ContractQuery
  contract: my_contract
  endpoint: my_query_endpoint
  arguments:
    # List<u8>
    - [0, 1, 2, 3]    

    # Tuple<TokenIdentifier, TokenIdentifier>            
    - [WEGLD-abcdef, MEX-abcdef]

    # Tuple<TokenIdentifier, TokenIdentifier>
    - - WEGLD-abcdef
      - MEX-abcdef   
```

## Structs

`Structs` must be provided simply as a list or a dictionary of their elements. The number of provided elements must exactly match the number of elements of the `Struct`. 

```rust
#[derive(TopEncode, TopDecode, NestedEncode, NestedDecode, TypeAbi, PartialEq, Eq)]
pub struct MyStruct<M: ManagedTypeApi> {
    pub int: u16,
    pub seq: ManagedVec<M, u8>,
    pub another_byte: u8,
    pub uint_32: u32,
    pub uint_64: u64,
}
```

```yaml
- type: ContractQuery
  contract: my_contract
  endpoint: my_query_endpoint
  arguments:
    # MyStruct provided as a list of elements using yaml syntax
    - - 8          
      - [9, 45]
      - 0
      - 789484
      - 485
    
    # MyStruct provided as a list of elements using a list syntax
    - [8, [9, 45], 0, 789484, 485] 

    # MyStruct provided as a dictionnary of elements using the field names
    - int: 8
      seq: [9, 45]
      another_byte: 0
      uint_32: 789484
      uint_64: 485
```

## Enums

`Enums` are handled as a special kind of `Structs`. If you have a classical simple `Enum`, you can just provided the name or the discriminant of the element you want to provide. you can also provide the element as if it was a struct, while providing either of the keys `__name__` and `__discriminant__`.

```rust
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
```

```yaml
- type: ContractQuery
  contract: my_contract
  endpoint: my_query_endpoint
  arguments:
    # DayOfWeek::Monday using the name
    - Monday 

    # DayOfWeek::Tuesday using the discriminant
    - 1  

    # DayOfWeek::Wednesday using a dictionnary with the name 
    - __name__: Wednesday 

    # DayOfWeek::Thursday using a dictionnary with the discriminant 
    - __disciminant__: 3  
```

In case you are dealing with a complex `Enum`, you will be forced to use the struct approach while specifying the custom values needed.

```rust
#[derive(TopEncode, TopDecode, NestedEncode, NestedDecode, TypeAbi, PartialEq, Eq)]
pub enum EnumWithEverything<M: ManagedTypeApi> {
    Default,
    Today(DayOfWeek),
    Write(ManagedVec<M, u8>, u16),
    MyStruct {
        int: u16,
        seq: ManagedVec<M, u8>,
        another_byte: u8,
        uint_32: u32,
        uint_64: u64,
    },
}
```

```yaml
- type: ContractQuery
  contract: my_contract
  endpoint: my_query_endpoint
  arguments:
    # EnumWithEverything::Default
    - Default

    # EnumWithEverything::Today::Tuesday as a list
    - - Today
      - Tuesday
    # EnumWithEverything::Today::Tuesday as a dictionnary
      - __name__: Today
        "0": Tuesday
    

    # EnumWithEverything::Write as a list
    - - Write
      - [1, 2, 4, 8]
      - 14
    # EnumWithEverything::Write as a dictionnary
    - __name__: Write
      "0": [1, 2, 4, 8]
      "1": 14
    
    # EnumWithEverything::MyStruct as a list
    - - MyStruct
      - 8
      - [9, 45]
      - 0
      - 789484
      - 485
    # EnumWithEverything::MyStruct as a dictionnary
    - __name__: MyStruct
      int: 8
      seq: [9, 45]
      another_byte: 0
      uint_32: 789484
      uint_64: 485
```

## MultiValueEncoded

When dealing with `MultiValueEncoded` types, the user must provide the elements as a list.
So if he wants to send three values as multi-encoded, he must provided a list of  three values.

```rust
#[view]
fn my_query_endpoint(&self, my_isize: isize, biguints: MultiValueEncoded<BigUint>) {}
```

```yaml
- type: ContractQuery
  contract: my_contract
  endpoint: my_query_endpoint
  arguments:
    - 4  # my_isize
    - - 178978798  # -> biguints[0]
      - 398835293  # -> biguints[1]
      - 105639583  # -> biguints[2]
      ...
      - 434782323  # -> biguints[n]
```

## OptionalValue

The sdk from the core team imposes to provide all values, even when they are optional. MxOps is forced to apply this constraint as well: Optional value must be provided. In case you want to specify that you send no value, write `null`.

```rust
#[view]
fn my_query_endpoint(
    &self,
    my_option_biguint: Option<BigUint>,
    my_optional_token_identifier_2: OptionalValue<TokenIdentifier>,
)
```

```yaml
- type: ContractQuery
  contract: my_contract
  endpoint: my_query_endpoint
  arguments:
    - 123987
    - null
```

## Option Value

For option values, just write a value of the expected type or `null`.

```rust
#[view]
fn my_query_endpoint(
    &self,
    my_option_biguint: Option<BigUint>,
)
```

```yaml
- type: ContractQuery
  contract: my_contract
  endpoint: my_query_endpoint
  arguments:
    - 123987

- type: ContractQuery
  contract: my_contract
  endpoint: my_query_endpoint
  arguments:
    - null
```