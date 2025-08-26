import json
from functools import cached_property
from typing import TypedDict

from .libconfsec.base import LibConfsecBase, ResponseHandle, ResponseStreamHandle


class KV(TypedDict):
    key: str
    value: str


class ResponseMetadata(TypedDict):
    status_code: int
    reason_phrase: str
    http_version: str
    url: str
    headers: list[KV]


class ResponseStream:
    def __init__(self, lc: LibConfsecBase, handle: ResponseStreamHandle) -> None:
        self._lc = lc
        self._handle = handle

    def get_next(self) -> bytes:
        return self._lc.response_stream_get_next(self._handle)

    def close(self) -> None:
        self._lc.response_stream_destroy(self._handle)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def __iter__(self):
        return self

    def __next__(self):
        data = self.get_next()
        if not data:
            raise StopIteration
        return data

    def __del__(self):
        self.close()


class Response:
    def __init__(self, lc: LibConfsecBase, handle: ResponseHandle) -> None:
        self._lc = lc
        self._handle = handle

    @cached_property
    def metadata(self) -> ResponseMetadata:
        return json.loads(self._lc.response_get_metadata(self._handle))

    @cached_property
    def body(self) -> bytes:
        return self._lc.response_get_body(self._handle)

    def get_stream(self) -> ResponseStream:
        handle = self._lc.response_get_stream(self._handle)
        return ResponseStream(self._lc, handle)

    def close(self) -> None:
        self._lc.response_destroy(self._handle)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def __del__(self):
        self.close()
