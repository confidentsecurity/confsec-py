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


class ConfsecSyncByteStream(SyncByteStream):
    def __init__(self, stream: ResponseStream) -> None:
        self._stream = stream

    def __iter__(self) -> Iterator[bytes]:
        return self._stream

    def close(self) -> None:
        self._stream.close()


class ConfsecTransport(BaseTransport):
    def __init__(self, client: "ConfsecClient") -> None:
        self._client = client

    def handle_request(self, request: Request) -> HttpxResponse:
        req_bytes = prepare_request(request)
        confsec_resp = self._client.do_request(req_bytes)
        resp_metadata = confsec_resp.metadata
        headers = [(h["key"], h["value"]) for h in resp_metadata["headers"]]

        body, stream = None, None
        if confsec_resp.is_streaming:
            stream = ConfsecSyncByteStream(confsec_resp.get_stream())
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
