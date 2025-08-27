import json

import pytest
from httpx import SyncByteStream

from confsec.client import ConfsecClient

URL = "http://confsec.invalid/api/generate"
MODEL = "llama3.2:1b"
HEADERS = {
    "Accept": "application/x-ndjson",
    "Content-Type": "application/json",
    "X-Confsec-Node-Tags": f"model={MODEL}",
}
PROMPT = "Count to ten in Spanish."


@pytest.mark.e2e
def test_httpx_e2e(api_key, env):
    with ConfsecClient(
        api_key=api_key, default_node_tags=[f"model={MODEL}"], env=env
    ) as client:
        httpx = client.get_http_client()

        # Do a non-streaming request.
        resp = httpx.post(
            URL,
            headers=HEADERS,
            json={"model": MODEL, "prompt": PROMPT, "stream": False},
        )
        assert resp.status_code == 200
        assert resp.json()["response"]

        # Do a streaming request.
        with httpx.stream(
            "POST",
            URL,
            headers=HEADERS,
            json={"model": MODEL, "prompt": PROMPT, "stream": True},
        ) as resp:
            assert resp.status_code == 200
            assert resp.headers["content-type"] == "application/x-ndjson"
            assert isinstance(resp.stream, SyncByteStream)

            chunks = []
            for line in resp.stream:
                assert line
                chunk = json.loads(line)["response"]
                chunks.append(chunk)

            assert len(chunks) > 1
