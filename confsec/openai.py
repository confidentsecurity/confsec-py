from __future__ import annotations

import os
from typing import TypedDict
from typing_extensions import NotRequired

from openai import OpenAI as _OpenAI
from openai.resources.chat import Chat
from openai.resources.completions import Completions

from .client import ConfsecClient
from .closeable import Closeable
from .libconfsec.base import IdentityPolicySource

_BASE_URL = "http://confsec.invalid/v1"


class ConfsecConfig(TypedDict):
    api_url: NotRequired[str]
    identity_policy_source: NotRequired[IdentityPolicySource]
    oidc_issuer: NotRequired[str]
    oidc_issuer_regex: NotRequired[str]
    oidc_subject: NotRequired[str]
    oidc_subject_regex: NotRequired[str]
    concurrent_requests_target: NotRequired[int]
    max_candidate_nodes: NotRequired[int]
    default_node_tags: NotRequired[list[str]]
    env: NotRequired[str]


class OpenAI(Closeable):
    """
    OpenAI-compatible client that routes requests through Confsec.

    Drop-in replacement for the OpenAI Python client that provides secure,
    anonymous access to AI models via the Confsec network.

    Args:
        api_key: Confsec API key (or None to use CONFSEC_API_KEY environment variable)
        confsec_config: Additional configuration for the Confsec client
    """

    chat: Chat
    completions: Completions

    def __init__(
        self, api_key: str | None = None, confsec_config: ConfsecConfig | None = None
    ):
        super().__init__()

        if api_key is None:
            api_key = os.environ["CONFSEC_API_KEY"]

        if confsec_config is None:
            confsec_config = {}

        if confsec_config.get("api_url") is None:
            raise ValueError("api_url is required for confsec_config")

        self._confsec_client = ConfsecClient(api_key=api_key, **confsec_config)
        self._openai_client = _OpenAI(
            api_key=api_key,
            base_url=_BASE_URL,
            http_client=self._confsec_client.get_http_client(),
        )

        self.chat = self._openai_client.chat
        self.completions = self._openai_client.completions

    @property
    def confsec_client(self) -> ConfsecClient:
        """
        Access the underlying ConfsecClient instance.

        Returns:
            The ConfsecClient used for routing requests
        """
        return self._confsec_client

    def _close(self):
        self._confsec_client.close()
