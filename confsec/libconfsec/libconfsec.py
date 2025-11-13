from __future__ import annotations

from .base import (
    ClientHandle,
    IdentityPolicySource,
    LibConfsecBase,
    ResponseHandle,
    ResponseStreamHandle,
)
from . import libconfsec_py as lcp  # type: ignore[attr-defined]


class LibConfsec(LibConfsecBase):
    def client_create(
        self,
        api_url: str,
        api_key: str,
        identity_policy_source: IdentityPolicySource,
        oidc_issuer: str,
        oidc_issuer_regex: str,
        oidc_subject: str,
        oidc_subject_regex: str,
        concurrent_requests_target: int,
        max_candidate_nodes: int,
        default_node_tags: list[str] | None,
        env: str,
    ) -> int:
        return lcp.confsec_client_create(
            api_url,
            api_key,
            identity_policy_source,
            oidc_issuer,
            oidc_issuer_regex,
            oidc_subject,
            oidc_subject_regex,
            concurrent_requests_target,
            max_candidate_nodes,
            default_node_tags,
            env,
        )

    def client_destroy(self, client_handle: ClientHandle) -> None:
        lcp.confsec_client_destroy(client_handle)

    def client_get_default_credit_amount_per_request(
        self, client_handle: ClientHandle
    ) -> int:
        return lcp.confsec_client_get_default_credit_amount_per_request(client_handle)

    def client_get_max_candidate_nodes(self, client_handle: ClientHandle) -> int:
        return lcp.confsec_client_get_max_candidate_nodes(client_handle)

    def client_get_default_node_tags(self, client_handle: ClientHandle) -> list[str]:
        return lcp.confsec_client_get_default_node_tags(client_handle)

    def client_set_default_node_tags(
        self, client_handle: ClientHandle, default_node_tags: list[str]
    ) -> None:
        lcp.confsec_client_set_default_node_tags(client_handle, default_node_tags)

    def client_get_wallet_status(self, client_handle: ClientHandle) -> str:
        return lcp.confsec_client_get_wallet_status(client_handle)

    def client_do_request(
        self, client_handle: ClientHandle, request: bytes
    ) -> ResponseHandle:
        return lcp.confsec_client_do_request(client_handle, request)

    def response_destroy(self, response_handle: ResponseHandle) -> None:
        lcp.confsec_response_destroy(response_handle)

    def response_is_streaming(self, response_handle: ResponseHandle) -> bool:
        return lcp.confsec_response_is_streaming(response_handle)

    def response_get_metadata(self, response_handle: ResponseHandle) -> str:
        return lcp.confsec_response_get_metadata(response_handle)

    def response_get_body(self, response_handle: ResponseHandle) -> bytes:
        return lcp.confsec_response_get_body(response_handle)

    def response_get_stream(
        self, response_handle: ResponseHandle
    ) -> ResponseStreamHandle:
        return lcp.confsec_response_get_stream(response_handle)

    def response_stream_destroy(
        self, response_stream_handle: ResponseStreamHandle
    ) -> None:
        lcp.confsec_response_stream_destroy(response_stream_handle)

    def response_stream_get_next(
        self, response_stream_handle: ResponseStreamHandle
    ) -> bytes:
        return lcp.confsec_response_stream_get_next(response_stream_handle)
