from unittest.mock import Mock, patch
from httpx import Request, URL

from confsec.client._httpx import (
    prepare_request,
    ConfsecHttpxSyncByteStream,
    ConfsecHttpxTransport,
)
from confsec.client.response import Response, ResponseStream


class TestPrepareRequest:
    def test_basic_http_request_formatting(self):
        url = URL("https://api.example.com/test")
        request = Request(
            "POST",
            url,
            headers={"Content-Type": "application/json"},
            content=b'{"test": "data"}',
        )

        result = prepare_request(request)

        expected = 'POST /test HTTP/1.1\r\nhost: api.example.com\r\ncontent-type: application/json\r\ncontent-length: 16\r\n\r\n{"test": "data"}'.encode(
            "utf-8"
        )
        assert result == expected

    def test_multiple_headers(self):
        url = URL("https://api.example.com/endpoint")
        request = Request(
            "GET",
            url,
            headers={
                "Authorization": "Bearer token123",
                "User-Agent": "test-client/1.0",
                "Accept": "application/json",
            },
            content=b"",
        )

        result = prepare_request(request)

        # Check that all headers are included (httpx uses lowercase)
        result_str = result.decode("utf-8")
        assert "GET /endpoint HTTP/1.1" in result_str
        assert "authorization: Bearer token123" in result_str
        assert "user-agent: test-client/1.0" in result_str
        assert "accept: application/json" in result_str
        assert result_str.endswith("\r\n\r\n")

    def test_empty_body(self):
        url = URL("https://api.example.com/test")
        request = Request("GET", url, content=b"")

        result = prepare_request(request)

        assert result.endswith(b"\r\n\r\n")


class TestConfsecHttpxSyncByteStream:
    def test_iter_returns_underlying_stream(self):
        mock_stream = Mock(spec=ResponseStream)
        byte_stream = ConfsecHttpxSyncByteStream(mock_stream)

        result = byte_stream.__iter__()

        assert result is mock_stream

    def test_close_calls_underlying_stream_close(self):
        mock_stream = Mock(spec=ResponseStream)
        byte_stream = ConfsecHttpxSyncByteStream(mock_stream)

        byte_stream.close()

        mock_stream.close.assert_called_once()


class TestConfsecHttpxTransport:
    def test_handle_request_non_streaming_response(self):
        mock_client = Mock()
        mock_response = Mock(spec=Response)
        mock_response.metadata = {
            "status_code": 200,
            "headers": [{"key": "Content-Type", "value": "application/json"}],
        }
        mock_response.is_streaming = False
        mock_response.body = b'{"result": "success"}'
        mock_client.do_request.return_value = mock_response

        transport = ConfsecHttpxTransport(mock_client)
        url = URL("https://api.example.com/test")
        request = Request("POST", url, content=b'{"test": "data"}')

        result = transport.handle_request(request)

        assert result.status_code == 200
        assert result.content == b'{"result": "success"}'
        assert ("content-type", "application/json") in result.headers.items()
        mock_response.close.assert_called_once()

    def test_handle_request_streaming_response(self):
        mock_client = Mock()
        mock_response = Mock(spec=Response)
        mock_stream = Mock(spec=ResponseStream)
        mock_response.metadata = {
            "status_code": 200,
            "headers": [{"key": "Content-Type", "value": "text/event-stream"}],
        }
        mock_response.is_streaming = True
        mock_response.get_stream.return_value = mock_stream
        mock_client.do_request.return_value = mock_response

        transport = ConfsecHttpxTransport(mock_client)
        url = URL("https://api.example.com/test")
        request = Request("POST", url, content=b'{"test": "data"}')

        result = transport.handle_request(request)

        assert result.status_code == 200
        assert isinstance(result.stream, ConfsecHttpxSyncByteStream)
        assert result.stream._stream is mock_stream
        mock_response.close.assert_not_called()

    def test_preprocess_request_openai_path(self):
        mock_client = Mock()
        transport = ConfsecHttpxTransport(mock_client)

        for url in [
            "https://api.openai.com/v1/completions",
            "https://api.openai.com/v1/chat/completions",
        ]:
            request = Request("POST", URL(url), content=b'{"model": "gpt-3.5-turbo"}')
            with patch.object(
                transport, "_maybe_add_model_tag", return_value=request
            ) as mock_add_tag:
                _ = transport._preprocess_request(request)
                mock_add_tag.assert_called_once_with(request)

    def test_preprocess_request_non_openai_path(self):
        mock_client = Mock()
        transport = ConfsecHttpxTransport(mock_client)

        url = URL("https://api.example.com/other/endpoint")
        request = Request("POST", url, content=b'{"data": "test"}')

        with patch.object(transport, "_maybe_add_model_tag") as mock_add_tag:
            result = transport._preprocess_request(request)
            mock_add_tag.assert_not_called()
            assert result is request


class TestModelTagInjection:
    def test_maybe_add_model_tag_valid_json_with_model(self):
        mock_client = Mock()
        transport = ConfsecHttpxTransport(mock_client)

        url = URL("https://api.openai.com/v1/completions")
        request = Request(
            "POST", url, content=b'{"model": "gpt-3.5-turbo", "prompt": "test"}'
        )

        result = transport._maybe_add_model_tag(request)

        assert result.headers["X-Confsec-Node-Tags"] == "model=gpt-3.5-turbo"

    def test_maybe_add_model_tag_invalid_json(self):
        mock_client = Mock()
        transport = ConfsecHttpxTransport(mock_client)

        url = URL("https://api.openai.com/v1/completions")
        request = Request("POST", url, content=b"invalid json {")

        result = transport._maybe_add_model_tag(request)

        assert result is request
        assert "X-Confsec-Node-Tags" not in result.headers

    def test_maybe_add_model_tag_missing_model_field(self):
        mock_client = Mock()
        transport = ConfsecHttpxTransport(mock_client)

        url = URL("https://api.openai.com/v1/completions")
        request = Request("POST", url, content=b'{"prompt": "test", "max_tokens": 100}')

        result = transport._maybe_add_model_tag(request)

        assert result is request
        assert "X-Confsec-Node-Tags" not in result.headers

    def test_maybe_add_model_tag_existing_header_no_duplicate(self):
        mock_client = Mock()
        transport = ConfsecHttpxTransport(mock_client)

        url = URL("https://api.openai.com/v1/completions")
        request = Request(
            "POST",
            url,
            headers={"X-Confsec-Node-Tags": "model=gpt-3.5-turbo,other=value"},
            content=b'{"model": "gpt-3.5-turbo", "prompt": "test"}',
        )

        result = transport._maybe_add_model_tag(request)

        assert (
            result.headers["X-Confsec-Node-Tags"] == "model=gpt-3.5-turbo,other=value"
        )

    def test_maybe_add_model_tag_existing_header_with_new_model(self):
        mock_client = Mock()
        transport = ConfsecHttpxTransport(mock_client)

        url = URL("https://api.openai.com/v1/completions")
        request = Request(
            "POST",
            url,
            headers={"X-Confsec-Node-Tags": "other=value"},
            content=b'{"model": "gpt-4", "prompt": "test"}',
        )

        result = transport._maybe_add_model_tag(request)

        assert result.headers["X-Confsec-Node-Tags"] == "other=value,model=gpt-4"

    def test_maybe_add_model_tag_doesnt_override_existing_model(self):
        mock_client = Mock()
        transport = ConfsecHttpxTransport(mock_client)

        url = URL("https://api.openai.com/v1/completions")
        request = Request(
            "POST",
            url,
            headers={"X-Confsec-Node-Tags": "model=gpt-3.5-turbo,other=value"},
            content=b'{"model": "gpt-4", "prompt": "test"}',
        )

        result = transport._maybe_add_model_tag(request)

        assert (
            result.headers["X-Confsec-Node-Tags"] == "model=gpt-3.5-turbo,other=value"
        )

    def test_maybe_add_model_tag_multiple_existing_tags(self):
        mock_client = Mock()
        transport = ConfsecHttpxTransport(mock_client)

        url = URL("https://api.openai.com/v1/completions")
        request = Request(
            "POST",
            url,
            headers={"X-Confsec-Node-Tags": "tag1=value1,tag2=value2,tag3=value3"},
            content=b'{"model": "gpt-3.5-turbo", "prompt": "test"}',
        )

        result = transport._maybe_add_model_tag(request)

        assert (
            result.headers["X-Confsec-Node-Tags"]
            == "tag1=value1,tag2=value2,tag3=value3,model=gpt-3.5-turbo"
        )
