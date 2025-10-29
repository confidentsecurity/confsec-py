<img width="200" height="auto" alt="Logo - Dark" src="https://github.com/user-attachments/assets/7b520fec-427e-4613-b173-abae8c4cd4c2" />

# Python SDK

## Overview

The CONFSEC Python SDK provides developers with a convenient way to make secure
and anonymous AI inference requests via CONFSEC. It can function as a drop-in
replacement for existing OpenAI clients, or as an HTTP client for lower-level
access to the CONFSEC API. Using the SDK, programs can make requests without the
need to deploy and manager the CONFSEC proxy.

## Installation

```bash
pip install confsec
```

## Quickstart

Use our OpenAI wrapper as a drop-in replacement for existing OpenAI clients:

```python
# Use OpenAI wrapper
from confsec.openai import OpenAI
client = OpenAI()
```

Or, for lower-level access, use the CONFSEC-enabled HTTP client directly:

```python
# Use HTTP client
import os
from confsec import ConfsecClient

with ConfsecClient(api_key=os.environ["CONFSEC_API_KEY"]) as client:
    http = client.get_http_client()
```

## Configuration

We aim to make the SDK as config-free as possible. However, there are some
parameters you can optionally configure to control how the client interacts
with the CONFSEC backend:

- `concurrent_requests_target (int)`: Allows the client to specify the desired
  request parallelism. This primarily impacts the number of credits that the
  client will maintain cached and available to use immediately. Higher values
  for this parameter will increase the maximum request throughput that the
  client can achieve, but also increases the amount of credits that may be lost
  permanently if the client process terminates without properly closing the
  client.
- `default_node_tags (list[str])`: Allows the client to specify default filters
  for CONFSEC compute nodes that will be applied to all requests. Users should
  not need to configure this in most cases, especially when using the OpenAI
  wrapper, since the `model` field of any request will be automatically mapped
  to the appropriate CONFSEC node tags.

## Usage

### OpenAI Wrapper

The `OpenAI` class can be initialized explicitly with an API key, by passing the
`api_key` parameter to the constructor. Otherwise, it will attempt to load the
API key from the `CONFSEC_API_KEY` environment variable.

It is very important to call `client.close()` when you are done with the client
to ensure that all resources are properly released. This can be done explicitly,
or by using the `OpenAI` class as a context manager. Failure to do so may result
in credits being lost.

Currently, the following subset of APIs are supported:
- Completions
- Chat

```python
import os
client = OpenAI()

stream = client.chat.completions.create(
    model="deepseek-r1:1.5b",
    messages=[
        {
            "role": "user",
            "content": "What is the meaning of life?",
        }
    ],
    stream=True,
)
for chunk in stream:
    print(chunk.choices[0].delta.content, end="")

client.close()
```

### HTTP Client

The `ConfsecClient` class can also be initialized explicitly for lower-level
access to the CONFSEC API. It's recommended to create an HTTP client using the
`get_http_client` method of the `ConfsecClient` class which will use the client
as the transport, instead of calling `ConfsecClient`'s methods directly.

As with the `OpenAI` class, it is very important to call `client.close()` when
you are done with the client to ensure that all resources are properly released.
This can be done explicitly, or by using the `ConfsecClient` class as a context
manager. Failure to do so may result in credits being lost.

```python
import os
from confsec import ConfsecClient

with ConfsecClient(api_key=os.environ["CONFSEC_API_KEY"]) as client:
    http = client.get_http_client()
    response = http.request(
        "POST",
        # Important: the base URL must be set to "https://confsec.invalid"
        "https://confsec.invalid/v1/chat/completions",
        json={
            "model": "deepseek-r1:1.5b",
            "messages": [
                {"role": "user", "content": "What is the meaning of life?"}
            ]
        }
    )
    print(response.json())
```


