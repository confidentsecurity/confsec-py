import json
from typing import TypedDict

from .libconfsec.base import LibConfsecBase, ClientHandle
from .response import Response


class WalletStatus(TypedDict):
    credits_spent: int
    credits_held: int
    credits_available: int


class ConfsecClient:
    def __init__(
        self,
        api_key: str,
        concurrent_requests_target: int = 0,
        max_candidate_nodes: int = 0,
        default_node_tags: list[str] | None = None,
        **kwargs,
    ) -> None:
        env = kwargs.get("env", "production")

        lc: LibConfsecBase
        if "libconfsec" in kwargs:
            lc = kwargs["libconfsec"]
            assert isinstance(self._lc, LibConfsecBase)
        else:
            lc = get_libconfsec()

        self._lc: LibConfsecBase = lc

        self._handle: ClientHandle = self._lc.client_create(
            api_key,
            concurrent_requests_target,
            max_candidate_nodes,
            default_node_tags,
            env,
        )

    @property
    def max_candidate_nodes(self) -> int:
        return self._lc.client_get_max_candidate_nodes(self._handle)

    @property
    def default_credit_amount_per_request(self) -> int:
        return self._lc.client_get_default_credit_amount_per_request(self._handle)

    @property
    def default_node_tags(self) -> list[str]:
        return self._lc.client_get_default_node_tags(self._handle)

    def set_default_node_tags(self, default_node_tags: list[str]) -> None:
        self._lc.client_set_default_node_tags(self._handle, default_node_tags)

    def get_wallet_status(self) -> WalletStatus:
        return json.loads(self._lc.client_get_wallet_status(self._handle))

    def do_request(self, request: bytes) -> Response:
        handle = self._lc.client_do_request(self._handle, request)
        return Response(self._lc, handle)

    def close(self):
        self._lc.client_destroy(self._handle)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()


def get_libconfsec() -> LibConfsecBase:
    from .libconfsec.libconfsec import LibConfsec

    return LibConfsec()
