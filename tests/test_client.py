import json
import pytest
from unittest.mock import Mock, patch

from confsec.client.client import ConfsecClient
from confsec.libconfsec.base import IdentityPolicySource, LibConfsecBase, ClientHandle

API_URL = "https://api.openpcc-example.com"
API_KEY = "test_api_key"


class TestConfsecClientInitialization:
    def test_uses_custom_libconfsec_when_provided(self):
        mock_lc = Mock(spec=LibConfsecBase)
        mock_handle = Mock(spec=ClientHandle)
        mock_lc.client_create.return_value = mock_handle

        client = ConfsecClient(API_URL, API_KEY, libconfsec=mock_lc)

        assert client._lc is mock_lc
        mock_lc.client_create.assert_called_once_with(
            API_URL,
            API_KEY,
            IdentityPolicySource.CONFIGURED,
            "",
            "",
            "",
            "",
            0,
            0,
            [],
            "prod",
        )

    @patch("confsec.client.client.get_libconfsec")
    def test_creates_default_libconfsec_when_not_provided(self, mock_get_libconfsec):
        mock_lc = Mock(spec=LibConfsecBase)
        mock_handle = Mock(spec=ClientHandle)
        mock_lc.client_create.return_value = mock_handle
        mock_get_libconfsec.return_value = mock_lc

        client = ConfsecClient(API_URL, API_KEY)

        mock_get_libconfsec.assert_called_once()
        assert client._lc is mock_lc

    def test_passes_parameters_correctly_to_client_create(self):
        mock_lc = Mock(spec=LibConfsecBase)
        mock_handle = Mock(spec=ClientHandle)
        mock_lc.client_create.return_value = mock_handle

        _ = ConfsecClient(
            API_URL,
            API_KEY,
            concurrent_requests_target=5,
            max_candidate_nodes=10,
            default_node_tags=["tag1", "tag2"],
            env="staging",
            libconfsec=mock_lc,
        )

        mock_lc.client_create.assert_called_once_with(
            API_URL,
            API_KEY,
            IdentityPolicySource.CONFIGURED,
            "",
            "",
            "",
            "",
            5,
            10,
            ["tag1", "tag2"],
            "staging",
        )

    def test_default_env_is_prod(self):
        mock_lc = Mock(spec=LibConfsecBase)
        mock_handle = Mock(spec=ClientHandle)
        mock_lc.client_create.return_value = mock_handle

        _ = ConfsecClient(API_URL, API_KEY, libconfsec=mock_lc)

        mock_lc.client_create.assert_called_once_with(
            API_URL,
            API_KEY,
            IdentityPolicySource.CONFIGURED,
            "",
            "",
            "",
            "",
            0,
            0,
            [],
            "prod",
        )


class TestWalletStatus:
    def test_get_wallet_status_parses_json_correctly(self):
        mock_lc = Mock(spec=LibConfsecBase)
        mock_handle = Mock(spec=ClientHandle)
        mock_lc.client_create.return_value = mock_handle

        wallet_data = {
            "credits_spent": 100,
            "credits_held": 50,
            "credits_available": 450,
        }
        mock_lc.client_get_wallet_status.return_value = json.dumps(wallet_data)

        client = ConfsecClient(API_URL, API_KEY, libconfsec=mock_lc)
        result = client.get_wallet_status()

        assert result == wallet_data
        assert isinstance(result, dict)
        mock_lc.client_get_wallet_status.assert_called_once_with(mock_handle)

    def test_get_wallet_status_handles_malformed_json(self):
        mock_lc = Mock(spec=LibConfsecBase)
        mock_handle = Mock(spec=ClientHandle)
        mock_lc.client_create.return_value = mock_handle
        mock_lc.client_get_wallet_status.return_value = "invalid json {"

        client = ConfsecClient(API_URL, API_KEY, libconfsec=mock_lc)

        with pytest.raises(json.JSONDecodeError):
            client.get_wallet_status()


class TestHttpClient:
    def test_get_http_client_creates_httpx_client_with_transport(self):
        mock_lc = Mock(spec=LibConfsecBase)
        mock_handle = Mock(spec=ClientHandle)
        mock_lc.client_create.return_value = mock_handle

        client = ConfsecClient(API_URL, API_KEY, libconfsec=mock_lc)

        with patch("httpx.Client") as mock_httpx_client, patch(
            "confsec.client._httpx.ConfsecHttpxTransport"
        ) as mock_transport:
            mock_transport_instance = Mock()
            mock_transport.return_value = mock_transport_instance
            mock_client_instance = Mock()
            mock_httpx_client.return_value = mock_client_instance

            result = client.get_http_client()

            mock_transport.assert_called_once_with(client)
            mock_httpx_client.assert_called_once_with(transport=mock_transport_instance)
            assert result is mock_client_instance

    def test_get_http_client_raises_for_unsupported_type(self):
        mock_lc = Mock(spec=LibConfsecBase)
        mock_handle = Mock(spec=ClientHandle)
        mock_lc.client_create.return_value = mock_handle

        client = ConfsecClient(API_URL, API_KEY, libconfsec=mock_lc)

        with pytest.raises(AssertionError):
            client.get_http_client("requests")  # type: ignore


class TestResourceManagement:
    def test_close_calls_client_destroy(self):
        mock_lc = Mock(spec=LibConfsecBase)
        mock_handle = Mock(spec=ClientHandle)
        mock_lc.client_create.return_value = mock_handle

        client = ConfsecClient(API_URL, API_KEY, libconfsec=mock_lc)
        client.close()

        mock_lc.client_destroy.assert_called_once_with(mock_handle)

    def test_context_manager_calls_close(self):
        mock_lc = Mock(spec=LibConfsecBase)
        mock_handle = Mock(spec=ClientHandle)
        mock_lc.client_create.return_value = mock_handle

        with ConfsecClient(API_URL, API_KEY, libconfsec=mock_lc) as _:
            pass

        mock_lc.client_destroy.assert_called_once_with(mock_handle)

    def test_multiple_close_calls_are_safe(self):
        mock_lc = Mock(spec=LibConfsecBase)
        mock_handle = Mock(spec=ClientHandle)
        mock_lc.client_create.return_value = mock_handle

        client = ConfsecClient(API_URL, API_KEY, libconfsec=mock_lc)
        client.close()
        client.close()  # Should not raise

        assert mock_lc.client_destroy.call_count == 1
