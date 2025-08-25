# confsec-py

This is the open-source Python SDK for Confident Security. It allows users to
make secure and anonymous AI inference requests via Confident Security, without
having to worry about the client implementation specifics. It should function as
a drop-in replacement for the OpenAI Python SDK.

## Architecture Decisions

- The SDK should consist mainly of two components:
  - A Python wrapper for the `libconfsec` C static library, which implements the
    core CONFSEC client functionality. The wrapper should be exposed as a
    regular HTTP client.
  - A wrapper for the OpenAI Python SDK, which uses the above HTTP client to
    make requests to Confident Security.

## Useful Commands

- `uv run pytest tests` -- run the tests
