import os
import pytest
from unittest.mock import AsyncMock, Mock, patch

from confsec.openai import AsyncOpenAI, OpenAI
from confsec.client.client import ConfsecClient

API_URL = "https://api.openpcc-example.com"
API_KEY = "test_api_key"


# Parametrize tests to run for both sync and async clients
@pytest.fixture(params=["sync", "async"])
def client_class_and_mocks(request):
    """Fixture that provides client class and appropriate mocks."""
    is_async = request.param == "async"

    if is_async:
        client_class = AsyncOpenAI
        openai_patch = "confsec.openai._AsyncOpenAI"
        http_method = "get_async_http_client"
        mock_type = AsyncMock
    else:
        client_class = OpenAI
        openai_patch = "confsec.openai._OpenAI"
        http_method = "get_http_client"
        mock_type = Mock

    with patch("confsec.openai.ConfsecClient") as mock_confsec_client, patch(
        openai_patch
    ) as mock_openai:
        mock_client_instance = Mock(spec=ConfsecClient)
        mock_confsec_client.return_value = mock_client_instance
        mock_http_client = mock_type()
        getattr(mock_client_instance, http_method).return_value = mock_http_client

        mock_openai_instance = mock_type()
        mock_openai_instance.chat = mock_type()
        mock_openai_instance.completions = mock_type()
        mock_openai.return_value = mock_openai_instance

        yield {
            "client_class": client_class,
            "mock_confsec_client": mock_confsec_client,
            "mock_client_instance": mock_client_instance,
            "mock_http_client": mock_http_client,
            "mock_openai": mock_openai,
            "mock_openai_instance": mock_openai_instance,
            "is_async": is_async,
        }


class TestOpenAIInitialization:
    def test_with_explicit_api_key(self, client_class_and_mocks):
        mocks = client_class_and_mocks
        client_class = mocks["client_class"]

        openai_client = client_class(
            api_key=API_KEY, confsec_config={"api_url": API_URL}
        )

        mocks["mock_confsec_client"].assert_called_once_with(
            api_url=API_URL, api_key=API_KEY
        )
        mocks["mock_openai"].assert_called_once_with(
            api_key=API_KEY,
            base_url="http://confsec.invalid/v1",
            http_client=mocks["mock_http_client"],
        )
        assert openai_client.chat is mocks["mock_openai_instance"].chat
        assert openai_client.completions is mocks["mock_openai_instance"].completions

    def test_with_environment_variable_api_key(self, client_class_and_mocks):
        mocks = client_class_and_mocks
        client_class = mocks["client_class"]

        with patch.dict(os.environ, {"CONFSEC_API_KEY": "env_api_key"}):
            _ = client_class(confsec_config={"api_url": API_URL})

            mocks["mock_confsec_client"].assert_called_once_with(
                api_url=API_URL, api_key="env_api_key"
            )
            mocks["mock_openai"].assert_called_once_with(
                api_key="env_api_key",
                base_url="http://confsec.invalid/v1",
                http_client=mocks["mock_http_client"],
            )

    @pytest.mark.parametrize("client_class", [OpenAI, AsyncOpenAI])
    def test_missing_api_key_raises_key_error(self, client_class):
        # Ensure CONFSEC_API_KEY is not in environment
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(KeyError, match="CONFSEC_API_KEY"):
                client_class()

    @pytest.mark.parametrize("client_class", [OpenAI, AsyncOpenAI])
    def test_missing_api_url_raises_value_error(self, client_class):
        with pytest.raises(ValueError, match="api_url"):
            client_class(api_key=API_KEY)

    def test_explicit_api_key_overrides_environment(self, client_class_and_mocks):
        mocks = client_class_and_mocks
        client_class = mocks["client_class"]

        with patch.dict(os.environ, {"CONFSEC_API_KEY": "env_api_key"}):
            _ = client_class(
                api_key="explicit_key", confsec_config={"api_url": API_URL}
            )

            mocks["mock_confsec_client"].assert_called_once_with(
                api_url=API_URL, api_key="explicit_key"
            )
            mocks["mock_openai"].assert_called_once_with(
                api_key="explicit_key",
                base_url="http://confsec.invalid/v1",
                http_client=mocks["mock_http_client"],
            )


class TestResourceManagement:
    def test_close_calls_confsec_client_close(self, client_class_and_mocks):
        mocks = client_class_and_mocks
        client_class = mocks["client_class"]

        openai_client = client_class(
            api_key=API_KEY, confsec_config={"api_url": API_URL}
        )
        openai_client.close()

        mocks["mock_client_instance"].close.assert_called_once()

    def test_context_manager_calls_close(self, client_class_and_mocks):
        mocks = client_class_and_mocks
        client_class = mocks["client_class"]

        with client_class(api_key=API_KEY, confsec_config={"api_url": API_URL}) as _:
            pass

        mocks["mock_client_instance"].close.assert_called_once()


class TestConfsecClientProperty:
    def test_confsec_client_property_returns_client_instance(
        self, client_class_and_mocks
    ):
        mocks = client_class_and_mocks
        client_class = mocks["client_class"]

        openai_client = client_class(
            api_key=API_KEY, confsec_config={"api_url": API_URL}
        )

        assert openai_client.confsec_client is mocks["mock_client_instance"]


class TestConfigurationEdgeCases:
    def test_partial_config(self, client_class_and_mocks):
        mocks = client_class_and_mocks
        client_class = mocks["client_class"]

        partial_config = {
            "api_url": API_URL,
            "concurrent_requests_target": 5,
            "env": "staging",
        }

        _ = client_class(api_key=API_KEY, confsec_config=partial_config)  # type: ignore

        mocks["mock_confsec_client"].assert_called_once_with(
            api_url=API_URL,
            api_key=API_KEY,
            concurrent_requests_target=5,
            env="staging",
        )
