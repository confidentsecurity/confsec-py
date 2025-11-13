import pytest
# import pdb

from confsec.openai import OpenAI

MODEL = "gpt-oss:20b"


@pytest.fixture(scope="module")
def client(env, api_url, api_key):
    _client = OpenAI(
        api_key=api_key,
        confsec_config={
            "api_url": api_url,
            "oidc_issuer_regex": "https://token.actions.githubusercontent.com",
            "oidc_subject_regex": "^https://github.com/confidentsecurity/T/.github/workflows.*",
            "default_node_tags": [f"model={MODEL}"],
            "env": env,
        },
    )
    yield _client
    _client.close()


@pytest.mark.e2e
def test_openai_completions_e2e(client):
    # pdb.set_trace()
    # Test non-streaming completion
    response = client.completions.create(
        model=MODEL,
        prompt="Count to three",
        stream=False,
    )
    # Response should have nonempty content
    assert len(response.choices) > 0
    assert response.choices[0].text

    # Test streaming completion
    stream = client.completions.create(
        model=MODEL,
        prompt="Count to ten",
        stream=True,
    )
    chunks = []
    for chunk in stream:
        # Each chunk should have nonempty content
        if len(chunk.choices) == 0:
            continue
        if chunk.choices[0].finish_reason is not None:
            chunks.append(chunk.choices[0].text)

    # Should have received at least one chunk
    assert len(chunks) > 0


@pytest.mark.e2e
def test_openai_chat_completions_e2e(client):
    # pdb.set_trace()
    # Test non-streaming chat completion
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": "Count to three"}],
        stream=False,
    )
    # Response should have nonempty content
    assert len(response.choices) > 0
    assert response.choices[0].message.content

    # Test streaming chat completion
    stream = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": "Count to ten"}],
        stream=True,
    )

    chunks = []
    for chunk in stream:
        # Each chunk should have nonempty content
        # assert len(chunk.choices) > 0
        if len(chunk.choices) == 0:
            continue
        if chunk.choices[0].finish_reason is not None:
            chunks.append(chunk.choices[0].delta.content)

    # Should have received at least one chunk
    assert len(chunks) > 0
