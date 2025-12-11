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
client = OpenAI(confsec_config={
    "api_url": "https://app.confident.security",
    "oidc_issuer_regex": "https://token.actions.githubusercontent.com",
    "oidc_subject_regex": "^https://github.com/confidentsecurity/T/.github/workflows.*",
})
```

Or, for lower-level access, use the CONFSEC-enabled HTTP client directly:

```python
# Use HTTP client
import os
from confsec import ConfsecClient

with ConfsecClient(
    api_url="https://app.confident.security",
    api_key=os.environ["CONFSEC_API_KEY"],
    oidc_issuer_regex="https://token.actions.githubusercontent.com",
    oidc_subject_regex="^https://github.com/confidentsecurity/T/.github/workflows.*",
) as client:
    http = client.get_http_client()
```

## Configuration

We aim to make the SDK as config-free as possible. However, there are some
parameters you can optionally configure to control how the client interacts
with the CONFSEC backend:

- `api_url (str)`: The URL for the service implementing the OpenPCC auth API.
- `identity_policy_source (int)`: Accepts values from the `IdentityPolicySource`
  enum. Controls the source of the identity policy that the client uses to
  validate the signing identity of artifacts in the OpenPCC transparency log. By
  default `IdentityPolicySource.CONFIGURED` is used, which requires the caller
  to configure at least one of `oidc_issuer` or `oidc_issuer_regex`, and at least
  one of `oidc_subject` or `oidc_subject_regex`. Alternatively, the caller could set
  this as `IdentityPolicySource.UNSAFE_REMOTE`, which allows the client to
  receive and trust the identity policy from the auth server. This is unsafe and
  should only be used in development environments.
- `oidc_issuer (str)`: The OIDC issuer to trust for OpenPCC transparency log
  artifacts.
- `oidc_issuer_regex (str)`: A regular expression matching the OIDC issuers to
  trust for OpenPCC transparency log artifacts. Can be used in place of
  `oidc_issuer` to trust multiple issuers.
- `oidc_subject (str)`: The OIDC subject to trust for OpenPCC transparency log
  artifacts.
- `oidcSubject_Regex (str)`: A regular expression matching the OIDC subjects to
  trust for OpenPCC transparency log artifacts. Can be used in place of
  `oidc_subject` to trust multiple subjects.
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
client = OpenAI(confsec_config={
    "api_url": "https://app.confident.security",
    "oidc_issuer_regex": "https://token.actions.githubusercontent.com",
    "oidc_subject_regex": "^https://github.com/confidentsecurity/T/.github/workflows.*",
})

stream = client.chat.completions.create(
    model="gemma3:1b",
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

For async usage, use the `AsyncOpenAI` class:

```python
from confsec.openai import AsyncOpenAI

async def main():
    client = AsyncOpenAI(confsec_config={
        "api_url": "https://app.confident.security",
        "oidc_issuer_regex": "https://token.actions.githubusercontent.com",
        "oidc_subject_regex": "^https://github.com/confidentsecurity/T/.github/workflows.*",
    })

    stream = await client.chat.completions.create(
        model="gemma3:1b",
        messages=[{"role": "user", "content": "What is the meaning of life?"}],
        stream=True,
    )
    async for chunk in stream:
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

with ConfsecClient(
    api_url="https://app.confident.security",
    api_key=os.environ["CONFSEC_API_KEY"],
    oidc_issuer_regex="https://token.actions.githubusercontent.com",
    oidc_subject_regex="^https://github.com/confidentsecurity/T/.github/workflows.*",
) as client:
    http = client.get_http_client()
    response = http.request(
        "POST",
        # Important: the base URL must be set to "https://confsec.invalid"
        "https://confsec.invalid/v1/chat/completions",
        json={
            "model": "gemma3:1b",
            "messages": [
                {"role": "user", "content": "What is the meaning of life?"}
            ]
        }
    )
    print(response.json())
```

For async usage, use `get_async_http_client`:

```python
import os
from confsec import ConfsecClient

async def main():
    with ConfsecClient(
        api_url="https://app.confident.security",
        api_key=os.environ["CONFSEC_API_KEY"],
        oidc_issuer_regex="https://token.actions.githubusercontent.com",
        oidc_subject_regex="^https://github.com/confidentsecurity/T/.github/workflows.*",
    ) as client:
        http = client.get_async_http_client()
        response = await http.request(
            "POST",
            "https://confsec.invalid/v1/chat/completions",
            json={
                "model": "gemma3:1b",
                "messages": [
                    {"role": "user", "content": "What is the meaning of life?"}
                ]
            }
        )
        print(response.json())
```


