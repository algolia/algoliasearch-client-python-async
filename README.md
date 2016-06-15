**This package is in its early stages please report any bug you find to help
us improve it**


# Algolia Asynchronous Python Client

This package is designed to replace the
[`algoliasearch`](https://github.com/algolia/algoliasearch-client-python)
package in asynchronous environments.

This package is only compatible with python 3.4 and onward.

## What it does

- Is compatible with python `asyncio`.

- Provide asynchronous alternatives to most of the client methods.
  All those methods are just suffixed by `_async` (`search_async`,
  `add_object_async`, etc.)

- Still provide synchronous versions of the methods.

- Uses `aiohttp` as the HTTP underlying library.

- Uses `__aexit__` to avoid manually closing `aiohttp` sessions with
  python >= 3.5.1.

## What it does **not**

- Implement the `browse`, `browse_all`, `delete_by_query` methods.

- Implement the `search_disjunctive_faceting` method.

- Support task canceling (yet).

## Installation and Dependencies

Most of the logic of the synchronous client is being used here, so this
client depends on the synchronous one. It also depends on `aiohttp`.

To install this package: `pip install algoliasearchasync`.

## Documentation

All the asynchronous functions have the same names as the synchronous ones
with `_async` appended. Synchronous methods keep the same name.

Arguments taken by the asynchronous functions are the same as the synchronous
one, for the documentation of the behavior of each function please see:

- [Synchronous python clinet](https://github.com/algolia/algoliasearch-client-python)

- [Algolia documentation](https://www.algolia.com/doc)

## Examples

With python >= 3.4

```python
import asyncio
from algoliasearchasync import ClientAsync

client = ClientAsync('<APP_ID>', '<API_KEY>')
index = client.init_index('<INDEX_NAME>')
terms = ['<TERM2>', '<TERM2>']

# Create two different asynchronous searches for '<TERM1>' and '<TERM2>'.
searches = [index.search_async(term) for term in terms]

loop = asyncio.get_event_loop()
# Start and wait for completion.
complete = loop.run_until_complete(asyncio.gather(*searches))

for term, search in zip(terms, complete):
    print('Results for: {}'.format(term))
    # Display the field '<FIELD>' of each result.
    print('\n'.join([h['<FIELD>'] for h in search['hits']]))

# Client must be closed manually.
loop.run_until_complete(client.close())
```

With python >= 3.5.1

```python
import asyncio
from algoliasearchasync import ClientAsync

# Define a coroutine to be able to use `async with`.
async def main(terms):
    # Scope the client for it to be closed automatically.
    async with ClientAsync('<APP_ID>', '<API_KEY>') as client:
        index = c.init_index('<INDEX_NAME>')
        # Create as many searches as there is terms.
        searches = [index.search_async(term) for term in terms]
        # Return the aggregated results.
        return await asyncio.gather(*searches)

terms = ['<TERM1>', '<TERM2>']
loop = asyncio.get_event_loop()
# Start and wait for the task to complete.
complete = loop.run_until_complete(main(terms))
for term, search in zip(terms, complete):
    print('Results for {}'.format(term))
    # Display the field '<FIELD>' of each result.
    print('\n'.join([h['<FIELD>'] for h in search['hits']]))
```
