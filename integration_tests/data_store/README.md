# Data Store

This integration test define a smart-contract that have a lot of different data structures
as inputs, outputs and storage. This test aims to make sure that serialization and deserialization is done correctly.

## Endpoints

To check that serialization and deserialization happens correctly, each endpoint will accept some data and save it in the storage only if it is equal to a hard-coded value.
This ensure that the data sent was correctly serialized.

## Views

Each endpoint will have its equivalent view. As we are sure of what has been written in the mappers thanks to the endpoints, using the views will allow us to check that queries/deserialization is done correctly.

## ABI or not ABI ?

To ensure compatibility with previous versions of MxOps, some tests will be done with ABI definition and some without it.