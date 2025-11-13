from __future__ import annotations

import json
from typing import Literal, TYPE_CHECKING, TypedDict

from .response import Response
from ..closeable import Closeable
from ..libconfsec.base import IdentityPolicySource, LibConfsecBase, ClientHandle

if TYPE_CHECKING:
    from httpx import Client as HttpxClient


HttpClientType = Literal["httpx"]


class WalletStatus(TypedDict):
    credits_spent: int
    credits_held: int
    credits_available: int


class ConfsecClient(Closeable):
    """
    Client for making requests via Confsec.

    Args:
        api_key: Your Confsec API key
        concurrent_requests_target: Target number of concurrent requests (0 for default)
        max_candidate_nodes: Maximum number of candidate nodes to consider (0 for default)
        default_node_tags: Default tags to use for node selection
        **kwargs: Additional configuration
    """

    def __init__(
        self,
        api_url: str,
        api_key: str,
        identity_policy_source: IdentityPolicySource = IdentityPolicySource.CONFIGURED,
        oidc_issuer: str = "",
        oidc_issuer_regex: str = "",
        oidc_subject: str = "",
        oidc_subject_regex: str = "",
        concurrent_requests_target: int = 0,
        max_candidate_nodes: int = 0,
        default_node_tags: list[str] | None = None,
        **kwargs,
    ) -> None:
        super().__init__()

        env = kwargs.get("env", "prod")

        lc: LibConfsecBase
        if "libconfsec" in kwargs:
            lc = kwargs["libconfsec"]
            assert isinstance(lc, LibConfsecBase)
        else:
            lc = get_libconfsec()

        self._lc: LibConfsecBase = lc

        self._handle: ClientHandle = self._lc.client_create(
            api_url,
            api_key,
            identity_policy_source,
            oidc_issuer,
            oidc_issuer_regex,
            oidc_subject,
            oidc_subject_regex,
            concurrent_requests_target,
            max_candidate_nodes,
            default_node_tags or [],
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
        """
        Set the default node tags for this client.

        Args:
            default_node_tags: List of tags to use for node selection
        """
        self._lc.client_set_default_node_tags(self._handle, default_node_tags)

    def get_wallet_status(self) -> WalletStatus:
        """
        Get the current wallet status including credits spent, held, and available.

        Returns:
            WalletStatus containing credit information
        """
        return json.loads(self._lc.client_get_wallet_status(self._handle))

    def do_request(self, request: bytes) -> Response:
        """
        Make a request via Confsec.

        Args:
            request: Raw HTTP request as bytes

        Returns:
            Response object for the request
        """
        handle = self._lc.client_do_request(self._handle, request)
        return Response(self._lc, handle)

    def get_http_client(
        self, http_client_type: HttpClientType = "httpx"
    ) -> "HttpxClient":
        """
        Get an HTTP client configured to use Confsec transport.

        Args:
            http_client_type: Type of HTTP client to create (currently only "httpx")

        Returns:
            Configured HTTP client instance
        """
        assert http_client_type == "httpx"

        from httpx import Client as HttpxClient
        from ._httpx import ConfsecHttpxTransport

        return HttpxClient(transport=ConfsecHttpxTransport(self))

    def _close(self):
        self._lc.client_destroy(self._handle)


def get_libconfsec() -> LibConfsecBase:
    from ..libconfsec.libconfsec import LibConfsec

    return LibConfsec()
