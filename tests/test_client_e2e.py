from __future__ import annotations

import json

import pytest

from confsec.client import ConfsecClient, Response


URL = "http://confsec.invalid/v1/completions"
API_URL = "https://app.confident.security"
MODEL = "gpt-oss:20b"
HEADERS = {
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
def test_client_e2e(env, api_url, api_key):
    def get_content_type(resp: Response) -> str:
        return [
            h["value"]
            for h in resp.metadata["headers"]
            if h["key"].lower() == "content-type"
        ][0]

    client_kwargs = {
        "oidc_issuer_regex": "https://token.actions.githubusercontent.com",
        "oidc_subject_regex": "^https://github.com/confidentsecurity/T/.github/workflows.*",
        "default_node_tags": [f"model={MODEL}"],
        "env": env,
    }

    with ConfsecClient(api_url=api_url, api_key=api_key, **client_kwargs) as client:
        # Check configs
        initial_credit_amount = client.default_credit_amount_per_request
        assert initial_credit_amount > 0
        assert client.max_candidate_nodes > 0
        assert len(client.default_node_tags) == 1
        assert client.get_wallet_status()["credits_spent"] == 0

        # Do a non-streaming request
        req = request("POST", URL, HEADERS, get_body(PROMPT))
        with client.do_request(req) as resp:
            # import pdb

            # pdb.set_trace()
            content_type = get_content_type(resp)
            body = json.loads(resp.body)
            assert "application/json" in content_type
            assert resp.metadata["status_code"] == 200
            assert "choices" in body
            assert len(body["choices"]) > 0

        # Do a streaming request
        body = b""
        chunks: list[str] = []
        req = request("POST", URL, HEADERS, get_body(PROMPT, stream=True))
        with client.do_request(req) as resp:
            content_type = get_content_type(resp)
            assert content_type == "text/event-stream"
            assert resp.metadata["status_code"] == 200
            with resp.get_stream() as stream:
                for chunk in stream:
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
            full_response = "".join(chunks).lower()
            assert len(full_response) > 0
