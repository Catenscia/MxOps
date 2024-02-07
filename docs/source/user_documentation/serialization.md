# Serialization

When interacting with the blockchain, a very important aspect to keep in mind is the data format, in particular when dealing with smart-contracts and when the data has a complex representation such as custom structures with nested elements. To make things easy for the user, `MxOps` will use ABI definitions to:
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

`bytes` are trickier as yaml don't support directly the bytes type. If your intention is to provided vector, list of elements, string or anything that should be converted to bytes, then you can write them in the original format and `MxOps` will convert them for you.

However, if you really need to pass pure bytes data, then you must use the following syntax: `bytes:<b64_encoded_data>`. Where `b64_encoded_data` is your bytes data in the b64 format.


```yaml
- type: ContractQuery
  contract: my_contract
  endpoint: my_query_endpoint
  arguments:
    - [1, 2, 4, 8]  # vec that will be converted to bytes
    - "bytes:AQIECA=="  # same bytes data but in the b64 format
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
    - [0, 1, 2, 3]  # List<u8>
    - - 0           # List<u8>
      - 1
      - 2
      - 3
    - [WEGLD-abcde, MEX-abcdef]  # Tuple<TokenIdentifier, TokenIdentifier>
    - - WEGLD-abcde              # Tuple<TokenIdentifier, TokenIdentifier>
      - MEX-abcdef
```

## Structs

`Structs` must be provided simply as a list of their elements. The number of provided elements must exactly match the number of elements of the `Struct`.

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
    - - 8          # MyStruct provided as a list of element using yaml syntax
      - [9, 45]
      - 0
      - 789484
      - 485
    - [8, [9, 45], 0, 789484, 485]  # or directly using a list syntax
```

## Enums

`Enums` are handled as a special kind of `Structs`. If you have a classical `Enum`, you can just provided the name or the discriminant of the element you want to provide. If you prefer, you can also provide the element as a struct, while providing either of both of the keys `name` and `discriminant`.

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
    - Monday  # enum DayOfWeek when directly specifying the name
    - 1       # Tuesday in the enum DayOfWeek when directly specifying the discriminant
    - name: Wednesday  # enum DayOfWeek when specifying the name
    - disciminant: 3  # Thursday in the enum DayOfWeek when specifying the discriminant
    - name: Friday   # enum DayOfWeek when specifying both the name and the discriminant
      discriminant: 4  
```

In case you are dealing with a complex `Enum`, you will be forced to use the struct approach while specifying the custom values needed.

```rust
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
```

```yaml
- type: ContractQuery
  contract: my_contract
  endpoint: my_query_endpoint
  arguments:
    - Default  # simple element, no need for anything else
    - name: Today
      values:  # the complex values are specified in a list under the keyword values
        - Tuesday
    - name: Write
      values:
        - [1, 2, 4, 8]
        - 14
    - name: Struct
      values:
        - 8
        - [9, 45]
        - 0
        - 789484
        - 485
```

## MultiValueEncoded

When dealing with `MultiValueEncoded` types, the user must provide the elements individually.
So if he wants to send three values as multi-encoded, he must provided three separate arguments.

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
    - 178978798  # -> biguints[0]
    - 398835293  # -> biguints[1]
    - 105639583  # -> biguints[2]
    ...
    - 434782323  # -> biguints[n]
```


