import json

import pytest
from httpx import SyncByteStream

from confsec.client import ConfsecClient

URL = "http://confsec.invalid/v1/completions"
MODEL = "gpt-oss:20b"
HEADERS = {
    "Accept": "application/x-ndjson",
    "Content-Type": "application/json",
    "X-Confsec-Node-Tags": f"model={MODEL}",
}
PROMPT = "Count to ten in Spanish."


@pytest.mark.e2e
def test_httpx_e2e(env, api_url, api_key):
    client_kwargs = {
        "oidc_issuer_regex": "https://token.actions.githubusercontent.com",
        "oidc_subject_regex": "^https://github.com/confidentsecurity/T/.github/workflows.*",
        "default_node_tags": [f"model={MODEL}"],
        "env": env,
    }

    with ConfsecClient(api_url=api_url, api_key=api_key, **client_kwargs) as client:
        httpx = client.get_http_client()

        # Do a non-streaming request.
        resp = httpx.post(
            URL,
            headers=HEADERS,
            json={"model": MODEL, "prompt": PROMPT, "stream": False},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "choices" in body
        assert len(body["choices"]) > 0

        # Do a streaming request.
        with httpx.stream(
            "POST",
            URL,
            headers=HEADERS,
            json={"model": MODEL, "prompt": PROMPT, "stream": True},
        ) as resp:
            assert resp.status_code == 200
            assert resp.headers["content-type"] == "text/event-stream"
            assert isinstance(resp.stream, SyncByteStream)

            body = b""
            chunks: list[str] = []
            for chunk in resp.stream:
                body += chunk
                lines = body.splitlines()
                if len(lines) <= 1:
                    continue

                for line in lines[:-1]:
                    line = line.decode("utf-8").strip().removeprefix("data: ")
                    if not line or line == "[DONE]":
                        continue
                    chunk_json = json.loads(line)
                    assert "choices" in chunk_json
                    if len(chunk_json["choices"]) > 0:
                        chunks.append(chunk_json["choices"][0]["text"])

                body = lines[-1]

            assert len(chunks) > 1
            full_response = "".join(chunks)
            assert len(full_response) > 0
