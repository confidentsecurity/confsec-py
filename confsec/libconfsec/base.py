from __future__ import annotations

from abc import ABC, abstractmethod
from enum import IntEnum


class IdentityPolicySource(IntEnum):
    CONFIGURED = 0
    UNSAFE_REMOTE = 1


ClientHandle = int
ResponseHandle = int
ResponseStreamHandle = int


class LibConfsecBase(ABC):
    """
    Base class defining the python interface for libconfsec.
    """

    @abstractmethod
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
    ) -> ClientHandle:
        """
        Create a new client.

        Args:
            api_url (str): The auth API URL to use.
            api_key (str): The API key to use for authentication.
            identity_policy_source (IdentityPolicySource): The identity policy source.
            oidc_issuer (str): The OIDC issuer.
            oidc_issuer_regex (str): The OIDC issuer regex.
            oidc_subject (str): The OIDC subject.
            oidc_subject_regex (str): The OIDC subject regex.
            concurrent_requests_target (int): The target number of concurrent requests.
            max_candidate_nodes (int): The maximum number of candidate nodes.
            default_node_tags (list[str] | None): The default node tags.
            env (str): The environment to use.

        Returns:
            ClientHandle: The client handle.
        """

    @abstractmethod
    def client_destroy(self, client_handle: ClientHandle) -> None:
        """
        Destroy a client.

        Args:
            client_handle (ClientHandle): The client handle.
        """

    @abstractmethod
    def client_get_default_credit_amount_per_request(
        self, client_handle: ClientHandle
    ) -> int:
        """
        Get the default credit amount per request.

        Args:
            client_handle (ClientHandle): The client handle.

        Returns:
            int: The default credit amount per request.
        """

    @abstractmethod
    def client_get_max_candidate_nodes(self, client_handle: ClientHandle) -> int:
        """
        Get the maximum number of candidate nodes.

        Args:
            client_handle (ClientHandle): The client handle.

        Returns:
            int: The maximum number of candidate nodes.
        """

    @abstractmethod
    def client_get_default_node_tags(self, client_handle: ClientHandle) -> list[str]:
        """
        Get the default node tags.

        Args:
            client_handle (ClientHandle): The client handle.

        Returns:
            list[str]: The default node tags.
        """

    @abstractmethod
    def client_set_default_node_tags(
        self, client_handle: ClientHandle, default_node_tags: list[str]
    ) -> None:
        """
        Set the default node tags.

        Args:
            client_handle (ClientHandle): The client handle.
            default_node_tags (list[str]): The default node tags.
        """

    @abstractmethod
    def client_get_wallet_status(self, client_handle: ClientHandle) -> str:
        """
        Get the wallet status.

        Args:
            client_handle (ClientHandle): The client handle.

        Returns:
            int: JSON string representing the wallet status.
        """

    @abstractmethod
    def client_do_request(
        self, client_handle: ClientHandle, request: bytes
    ) -> ResponseHandle:
        """
        Do an HTTP request.

        Args:
            client_handle (ClientHandle): The client handle.
            request (bytes): The raw HTTP request.

        Returns:
            ResponseHandle: The response handle.
        """

    @abstractmethod
    def response_destroy(self, response_handle: ResponseHandle) -> None:
        """
        Destroy a response.

        Args:
            response_handle (ResponseHandle): The response handle.
        """

    @abstractmethod
    def response_is_streaming(self, response_handle: ResponseHandle) -> bool:
        """
        Check if the response body is a stream.

        Args:
            response_handle (ResponseHandle): The response handle.

        Returns:
            bool: True if the response is a stream, False otherwise.
        """

    @abstractmethod
    def response_get_metadata(self, response_handle: ResponseHandle) -> str:
        """
        Get the response metadata.

        Args:
            response_handle (ResponseHandle): The response handle.

        Returns:
            str: JSON string representing the response metadata.
        """

    @abstractmethod
    def response_get_body(self, response_handle: ResponseHandle) -> bytes:
        """
        Get the response body. Throws an error if the response is a stream.

        Args:
            response_handle (ResponseHandle): The response handle.

        Returns:
            bytes: The response body.
        """

    @abstractmethod
    def response_get_stream(
        self, response_handle: ResponseHandle
    ) -> ResponseStreamHandle:
        """
        Get the response body stream. Throws an error if the response is not a stream.

        Args:
            response_handle (ResponseHandle): The response handle.

        Returns:
            ResponseStreamHandle: The response body stream handle.
        """

    @abstractmethod
    def response_stream_destroy(
        self, response_stream_handle: ResponseStreamHandle
    ) -> None:
        """
        Destroy a response stream.

        Args:
            response_stream_handle (ResponseStreamHandle): The response stream handle.
        """

    @abstractmethod
    def response_stream_get_next(
        self, response_stream_handle: ResponseStreamHandle
    ) -> bytes:
        """
        Read the next chunk from a response stream. Raises StopIteration when the stream is exhausted.

        Args:
            response_stream_handle (ResponseStreamHandle): The response stream handle.

        Returns:
            bytes: The read bytes.
        """
