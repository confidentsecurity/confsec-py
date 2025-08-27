import json

import pytest

from confsec.client import ConfsecClient
from confsec.response import Response


URL = "http://confsec.invalid/api/generate"
MODEL = "llama3.2:1b"
HEADERS = {
    "Accept": "application/x-ndjson",
    "Content-Type": "application/json",
    "X-Confsec-Node-Tags": f"model={MODEL}",
}
PROMPT = "Count to ten in Spanish."


def get_body(prompt: str, stream: bool = False) -> bytes:
    return json.dumps(
        {
            "model": MODEL,
            "stream": stream,
            "prompt": prompt,
        }
    ).encode("utf-8")


def request(method: str, url: str, headers: dict[str, str], body: bytes) -> bytes:
    if bool(body) and ("Content-Length" not in headers):
        headers = {**headers, "Content-Length": str(len(body))}

    request_line = f"{method} {url} HTTP/1.1\r\n"
    header_lines = "\r\n".join([f"{k}: {v}" for k, v in headers.items()])

    req_bytes = (request_line + header_lines + "\r\n\r\n").encode("utf-8")
    if body:
        req_bytes += body

    return req_bytes


@pytest.mark.e2e
def test_client_e2e(api_key, env):
    def get_content_type(resp: Response) -> str:
        return [
            h["value"] for h in resp.metadata["headers"] if h["key"] == "Content-Type"
        ][0]

    with ConfsecClient(
        api_key=api_key, default_node_tags=[f"model={MODEL}"], env=env
    ) as client:
        # Check configs
        initial_credit_amount = client.default_credit_amount_per_request
        assert initial_credit_amount > 0
        assert client.max_candidate_nodes > 0
        assert len(client.default_node_tags) == 1
        assert client.get_wallet_status()["credits_spent"] == 0

        # Do a non-streaming request
        req = request("POST", URL, HEADERS, get_body(PROMPT))
        with client.do_request(req) as resp:
            content_type = get_content_type(resp)
            body = json.loads(resp.body)
            assert "application/json" in content_type
            assert resp.metadata["status_code"] == 200
            assert "response" in body
            assert len(body["response"]) > 0

        # Do a streaming request
        chunks: list[str] = []
        req = request("POST", URL, HEADERS, get_body(PROMPT, stream=True))
        with client.do_request(req) as resp:
            content_type = get_content_type(resp)
            assert content_type == "application/x-ndjson"
            assert resp.metadata["status_code"] == 200
            with resp.get_stream() as stream:
                for chunk in stream:
                    chunk_json = json.loads(chunk)
                    print(chunk_json)
                    assert "response" in chunk_json
                    chunks.append(chunk_json["response"])

            assert len(chunks) > 1
            full_response = "".join(chunks).lower()
            assert len(full_response) > 0
