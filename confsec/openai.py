import os
from typing import NotRequired, TypedDict

from openai import OpenAI as _OpenAI
from openai.resources.chat import Chat
from openai.resources.completions import Completions

from .client import ConfsecClient
from .closeable import Closeable

_BASE_URL = "http://confsec.invalid/v1"


class ConfsecConfig(TypedDict):
    concurrent_requests_target: NotRequired[int]
    max_candidate_nodes: NotRequired[int]
    default_node_tags: NotRequired[list[str]]
    env: NotRequired[str]


class OpenAI(Closeable):
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
        return self._confsec_client

    def _close(self):
        self._confsec_client.close()
