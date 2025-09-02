import json
from typing import TYPE_CHECKING, Iterator

from httpx import BaseTransport, Request, Response as HttpxResponse, SyncByteStream

from .response import ResponseStream

if TYPE_CHECKING:
    from .client import ConfsecClient


def prepare_request(request: Request) -> bytes:
    """
    Create a raw HTTP request from an `httpx.Request` object.

    Args:
        request (Request): The `httpx.Request` object to convert.

    Returns:
        bytes: The raw HTTP request.
    """
    request_line = f"{request.method} {request.url.path} HTTP/1.1"
    headers = "\r\n".join(f"{k}: {v}" for k, v in request.headers.items())
    body = request.content
    return f"{request_line}\r\n{headers}\r\n\r\n".encode("utf-8") + body


class ConfsecHttpxSyncByteStream(SyncByteStream):
    def __init__(self, stream: ResponseStream) -> None:
        self._stream = stream

    def __iter__(self) -> Iterator[bytes]:
        return self._stream

    def close(self) -> None:
        self._stream.close()


class ConfsecHttpxTransport(BaseTransport):
    _openai_completions_path = "/v1/completions"
    _openai_chat_completions_path = "/v1/chat/completions"

    def __init__(self, client: "ConfsecClient") -> None:
        self._client = client

    def handle_request(self, request: Request) -> HttpxResponse:
        request = self._preprocess_request(request)

        req_bytes = prepare_request(request)
        confsec_resp = self._client.do_request(req_bytes)
        resp_metadata = confsec_resp.metadata
        headers = [(h["key"], h["value"]) for h in resp_metadata["headers"]]

        body, stream = None, None
        if confsec_resp.is_streaming:
            stream = ConfsecHttpxSyncByteStream(confsec_resp.get_stream())
        else:
            body = confsec_resp.body
            confsec_resp.close()

        return HttpxResponse(
            status_code=resp_metadata["status_code"],
            headers=headers,
            content=body,
            stream=stream,
            request=request,
        )

    def _preprocess_request(self, request: Request) -> Request:
        if request.url.path == self._openai_completions_path:
            request = self._maybe_add_model_tag(request)
        if request.url.path == self._openai_chat_completions_path:
            request = self._maybe_add_model_tag(request)

        return request

    def _maybe_add_model_tag(self, request: Request) -> Request:
        try:
            body = json.loads(request.content.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            # Not a JSON request, so we can't extract the model
            return request

        # Likewise, if the model is not specified in the body, exit early
        if "model" not in body:
            return request

        header: str
        tag = f"model={body['model']}"
        existing_header = request.headers.get("X-Confsec-Node-Tags", "")
        if existing_header:
            existing_tags = existing_header.split(",")
            if any(t.startswith("model=") for t in existing_tags):
                header = existing_header
            else:
                header = f"{existing_header},{tag}"
        else:
            header = tag

        request.headers["X-Confsec-Node-Tags"] = header
        return request
