from __future__ import annotations

import json
from functools import cached_property
from typing import Iterator, TypedDict

from ..closeable import Closeable
from ..libconfsec.base import LibConfsecBase, ResponseHandle, ResponseStreamHandle


class KV(TypedDict):
    key: str
    value: str


class ResponseMetadata(TypedDict):
    status_code: int
    reason_phrase: str
    http_version: str
    url: str
    headers: list[KV]


class ResponseStream(Closeable):
    """
    Streaming response from a Confsec request.

    Provides an iterator interface for reading streaming response data.
    """

    def __init__(
        self, lc: LibConfsecBase, resp: "Response", handle: ResponseStreamHandle
    ) -> None:
        super().__init__()
        self._lc = lc
        # Need to hold a reference to the response to keep it alive
        self._resp: "Response | None" = resp
        self._handle = handle

    def get_next(self) -> bytes:
        """
        Get the next chunk of streaming data.

        Returns:
            Next chunk as bytes, or empty bytes if stream is finished
        """
        return self._lc.response_stream_get_next(self._handle)

    def _close(self) -> None:
        self._lc.response_stream_destroy(self._handle)
        # Release the reference to the response
        self._resp = None

    def __iter__(self) -> Iterator[bytes]:
        return self

    def __next__(self) -> bytes:
        data = self.get_next()
        if not data:
            raise StopIteration
        return data

    def __del__(self):
        self.close()


class Response(Closeable):
    """
    Response from a Confsec request.

    Provides access to response metadata, body data, and streaming capabilities.
    """

    def __init__(self, lc: LibConfsecBase, handle: ResponseHandle) -> None:
        super().__init__()
        self._lc = lc
        self._handle = handle

    @cached_property
    def metadata(self) -> ResponseMetadata:
        return json.loads(self._lc.response_get_metadata(self._handle))

    @cached_property
    def is_streaming(self) -> bool:
        return self._lc.response_is_streaming(self._handle)

    @cached_property
    def body(self) -> bytes:
        return self._lc.response_get_body(self._handle)

    def get_stream(self) -> ResponseStream:
        """
        Get a streaming interface for this response.

        Returns:
            ResponseStream for iterating over response data
        """
        handle = self._lc.response_get_stream(self._handle)
        return ResponseStream(self._lc, self, handle)

    def _close(self) -> None:
        self._lc.response_destroy(self._handle)

    def __del__(self):
        self.close()
