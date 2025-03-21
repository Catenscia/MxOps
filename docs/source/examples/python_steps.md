# Python Steps Examples

This section will show you some basic ways of using the {doc}`PythonStep<../user_documentation/steps>`. These are just small examples: the python `Step` really gives you the keys to execute whatever you want: the creativity is yours to make what will perfectly fits your needs! 💪

## Calculation

Let's say we have a pool and we want to deposit two tokens to this pool and we want to send the tokens with same ratio as the current pool price.
To do this, we can create the following {doc}`Scene<../user_documentation/scenes>`:

```{code-block} yaml
:caption: my_scene.yaml

allowed_networks:
  - localnet
  - devnet

allowed_scenario:
  - ".*"

accounts:
  - account_id: alice  
    pem_path: ./wallets/alice.pem

steps:
  # fetch data from the pool and save it
  - type: ContractQuery
    contract: my_pool
    endpoint: GetBaseToken
    results_types:
      - type: TokenIdentifier
    results_save_keys: BaseToken # -> will be accessible with "%my_pool.BaseToken"

  - type: ContractQuery
    contract: my_pool
    endpoint: GetQuoteToken
    results_types:
      - type: TokenIdentifier
    results_save_keys: QuoteToken # -> will be accessible with "%my_pool.QuoteToken"
  
  - type: ContractQuery
    contract: my_pool
    endpoint: GetPoolPrice
    results_types:
      - type: BigUint
    results_save_keys: PoolPrice # -> will be accessible with "%my_pool.PoolPrice"

  # execute the python function to compute the amount of quote token to deposit
  # given the price and the base amount
  - type: Python
    module_path: ./folder/my_module.py
    function: compute_deposit_amount
    keyword_arguments:  # optional
      pool_price: "%my_pool.PoolPrice"
      base_amount: 1000000000000000000  # 1 assuming 18 decimals
    result_save_key: computed_quote_amount # -> will be accessible with "%computed_quote_amount"

  # deposit into the pool
  - type: ContractCall
    sender: alice
    contract: my_pool
    endpoint: deposit
    gas_limit: 60000000
    esdt_transfers:
      - token_identifier: "%my_pool.BaseToken"
        amount: 1000000000000000000
        nonce: 0
      - token_identifier: "%my_pool.QuoteToken"
        amount: "%computed_quote_amount"
        nonce: 0
```

During the python `Step`, MxOps will call a python function `compute_deposit_amount` that we can implement like this:

```{code-block} python
:caption: my_module.py

def compute_deposit_amount(pool_price: int, base_amount: int) -> str:
    """
    Compute the quote amount to send to a pool for a deposit.
    We assume that base and quote amounts are tokens with 18 decimals and
    that the pool price is multiplied by 10e12 (for safe division)

    :param pool_price: price of the pool (1 base = price/10e12 quote)
    :type pool_price: int
    :param base_amount: amount of base token to convert
    :type base_amount: int
    :return: quote amount equivalent the the provided base amount
    :rtype: int
    """
    quote_amount = base_amount * pool_price // 10**12
    return quote_amount
```

This python function helps us to make a calculation that is not directly supported by MxOps. The result is saved under the Scenario variable `computed_quote_amount`, as we specified in the `Step` definition, and it can be used in later steps, as shown above.

The user can also directly save values from the function within a Scenario:

```{code-block} python

scenario_data = ScenarioData.get()
scenario_data.set_value("key_1", 7894) # -> accessible with "%key_1"
scenario_data.set_value("key_2", "test-string") # -> accessible with "%key_2"

```


## Query, Calculation and Transaction

Alternatively, we can also realize all the actions of the previous example in python. This would look like this:

```{code-block} yaml
:caption: my_scene.yaml

allowed_networks:
  - localnet
  - devnet

allowed_scenario:
  - ".*"

accounts:
  - account_id: alice  
    pem_path: ./wallets/alice.pem

steps:
  - type: Python
    module_path: ./folder/my_module.py
    function: do_balanced_deposit
    keyword_arguments:
      contract: my_pool
      base_amount: 1000000000000000000  # 1 assuming 18 decimals
```

There is now only one `Step` in our `Scene`, as everything will be done in our python module below:

```{code-block} python
:caption: my_module.py

from typing import Tuple
from mxops.execution.msc import EsdtTransfer
from mxops.execution.steps import ContractCallStep, ContractQueryStep


def fetch_pool_data(contract: str) -> Tuple[int, str, str]:
    """
    Query a pool contract on the views GetPoolPrice, GetBaseToken and GetQuoteToken.
    Return the results of the queries

    :param contract: designation of the pool contract (id or address)
    :type contract: str
    :return: pool price, base token identifier and quote token identifier
    :rtype: Tuple[int, str, str]
    """
    # construct the queries
    price_query = ContractQueryStep(
        contract=contract,
        endpoint="GetPoolPrice",
        results_types=[{"type": "BigUint}]
    )
    base_token_query = ContractQueryStep(
        contract=contract,
        endpoint="GetBaseToken",
        results_types=[{"type": "TokenIdentifier}]
    )
    quote_token_query = ContractQueryStep(
        contract=contract,
        endpoint="GetQuoteToken",
        results_types=[{"type": "TokenIdentifier}]
    )

    # execute them
    price_query.execute()
    base_token_query.execute()
    quote_token_query.execute()
    
    # extract the results (we expect to have exactly one result per query)
    pool_price = price_query.decoded_results[0]
    base_token = base_token_query.decoded_results[0]
    quote_token = quote_token_query.decoded_results[0]
    return pool_price, base_token, quote_token


def do_balanced_deposit(contract: str, base_amount: int) -> str:
    """
    Given a base token amount, execute a balanced deposit to provided pool

    :param contract: designation of the pool contract (id or address)
    :type contract: str
    :param base_amount: amount of base token to convert
    :type base_amount: int
    """
    # fetch the current pool price and the token identifiers
    pool_price, base_token, quote_token = fetch_pool_data(contract)

    # compute the quote amount
    quote_amount = base_amount * pool_price // 10**12
    
    # create the contract call to deposit
    contract_call_step = ContractCallStep(
        contract="my_pool",
        endpoint="deposit",
        gas_limit=60000000,
        esdt_transfers=[
            EsdtTransfer(
                token_identifier=base_token,
                amount=base_amount
            ),
            EsdtTransfer(
                token_identifier=quote_token,
                amount=quote_amount
            )
        ]
    )

    # execute the transaction (the success check is included by default)
    contract_call_step.execute()

```

Both the previous and the current examples end up sending the same transaction: MxOps allows you to choose if you want to use native `Steps` or if you want to write everything yourself in python, which gives you more flexibility (at the cost of more work and responsibility).

## Third Party Interaction

You might want to interact with third parties for many reasons:
  - backend servers (e.g. a game engine)
  - oracles
  - databases (e.g. list of addresses for an airdrop)
  - ...

Using the python `Step`, you can easily integrate these third parties within the MxOps framework, as shown below.

```{code-block} yaml
:caption: my_scene.yaml

allowed_networks:
  - localnet
  - devnet

allowed_scenario:
  - ".*"

steps:
  - type: Python
    module_path: ./folder/my_module.py
    function: interact
```

```{code-block} python
:caption: my_module.py

import os
from mxops.data.data import ScenarioData

def interact():
    """
    A function that makes interactions between MxOps data and third parties
    """
    # fetch some data from MxOps
    scenario_data = ScenarioData.get()
    var_1 = scenario_data.get_contract_value("my_contract", "my_value_1")
    var_2 = scenario_data.get_token_value("my_token", "my_value_A")

    # interact with third parties
    # <write anything here>

    # save some data within MxOps
    scenario_data.set_contract_value("my_contract", "value_from_3rd_party", new_value_1) # -> now accessible with "%my_contract.value_from_3rd_party"
    scenario_data.get_token_value("my_token", "value_from_3rd_party", new_value_A) # -> now accessible with "%my_token.value_from_3rd_party"

    # or save it as an env var
    os.environ["MY_THIRD_PARTY_DATA"] = new_value_1  # -> now accessible with "$MY_THIRD_PARTY_DATA"
```

## Custom Check

You may want to run custom checks after some crucial actions. To do so, implement them in python and run them any time you want using the python `Step`. Within your custom function, you can make queries, access the MxOps data, use the api or proxy network provider and much more.

```{code-block} yaml
:caption: my_scene.yaml

allowed_networks:
  - localnet
  - devnet

allowed_scenario:
  - ".*"

steps:
  - type: Python
    module_path: ./folder/my_module.py
    function: custom_check
```

```{code-block} python
:caption: my_module.py

from multiversx_sdk_network_providers import ProxyNetworkProvider
from mxops.config.config import Config
from mxops.data.data import ScenarioData

class MyCustomException(Exception):
  pass

def custom_check():
    """
    A function that raise an error if custom conditions are not verified
    """
    # fetch some data from MxOps if you need
    scenario_data = ScenarioData.get()
    var_1 = scenario_data.get_contract_value("my_contract", "my_value_1")
    var_2 = scenario_data.get_token_value("my_token", "my_value_A")

    # make requests using the proxy if needed
    config = Config.get_config()
    proxy = ProxyNetworkProvider(config.get("PROXY"))
    # proxy.get_...

    # interact with third parties
    # <write anything here>

    # assert what you want
    assert condition

    # or directly raise a custom error
    if condition_2:
      raise MyCustomException
```
