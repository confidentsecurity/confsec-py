import json
import pytest
from unittest.mock import Mock

from confsec.client.response import Response, ResponseStream
from confsec.libconfsec.base import LibConfsecBase, ResponseHandle, ResponseStreamHandle


class TestResponse:
    def test_metadata_parses_json_correctly(self):
        mock_lc = Mock(spec=LibConfsecBase)
        mock_handle = Mock(spec=ResponseHandle)

        metadata_data = {
            "status_code": 200,
            "reason_phrase": "OK",
            "http_version": "HTTP/1.1",
            "url": "https://api.example.com",
            "headers": [{"key": "Content-Type", "value": "application/json"}],
        }
        mock_lc.response_get_metadata.return_value = json.dumps(metadata_data)

        response = Response(mock_lc, mock_handle)
        result = response.metadata

        assert result == metadata_data
        assert isinstance(result, dict)
        mock_lc.response_get_metadata.assert_called_once_with(mock_handle)

    def test_metadata_handles_malformed_json(self):
        mock_lc = Mock(spec=LibConfsecBase)
        mock_handle = Mock(spec=ResponseHandle)
        mock_lc.response_get_metadata.return_value = "invalid json {"

        response = Response(mock_lc, mock_handle)

        with pytest.raises(json.JSONDecodeError):
            _ = response.metadata

    def test_metadata_cached_property_behavior(self):
        mock_lc = Mock(spec=LibConfsecBase)
        mock_handle = Mock(spec=ResponseHandle)

        metadata_data = {
            "status_code": 200,
            "reason_phrase": "OK",
            "http_version": "HTTP/1.1",
            "url": "https://api.example.com",
            "headers": [],
        }
        mock_lc.response_get_metadata.return_value = json.dumps(metadata_data)

        response = Response(mock_lc, mock_handle)

        # First access
        result1 = response.metadata
        # Second access
        result2 = response.metadata

        # Should be the same object and only called once
        assert result1 is result2
        mock_lc.response_get_metadata.assert_called_once_with(mock_handle)

    def test_get_stream_creates_response_stream_with_correct_parameters(self):
        mock_lc = Mock(spec=LibConfsecBase)
        mock_handle = Mock(spec=ResponseHandle)
        mock_stream_handle = Mock(spec=ResponseStreamHandle)
        mock_lc.response_get_stream.return_value = mock_stream_handle

        response = Response(mock_lc, mock_handle)
        stream = response.get_stream()

        assert isinstance(stream, ResponseStream)
        assert stream._lc is mock_lc
        assert stream._resp is response
        assert stream._handle is mock_stream_handle
        mock_lc.response_get_stream.assert_called_once_with(mock_handle)

    def test_close_calls_response_destroy(self):
        mock_lc = Mock(spec=LibConfsecBase)
        mock_handle = Mock(spec=ResponseHandle)

        response = Response(mock_lc, mock_handle)
        response.close()

        mock_lc.response_destroy.assert_called_once_with(mock_handle)

    def test_context_manager_calls_close(self):
        mock_lc = Mock(spec=LibConfsecBase)
        mock_handle = Mock(spec=ResponseHandle)

        with Response(mock_lc, mock_handle) as _:
            pass

        mock_lc.response_destroy.assert_called_once_with(mock_handle)


class TestResponseStream:
    def test_iter_returns_self(self):
        mock_lc = Mock(spec=LibConfsecBase)
        mock_response = Mock(spec=Response)
        mock_handle = Mock(spec=ResponseStreamHandle)

        stream = ResponseStream(mock_lc, mock_response, mock_handle)

        assert iter(stream) is stream

    def test_next_calls_get_next_and_returns_data(self):
        mock_lc = Mock(spec=LibConfsecBase)
        mock_response = Mock(spec=Response)
        mock_handle = Mock(spec=ResponseStreamHandle)
        mock_lc.response_stream_get_next.return_value = b"test data"

        stream = ResponseStream(mock_lc, mock_response, mock_handle)
        result = next(stream)

        assert result == b"test data"
        mock_lc.response_stream_get_next.assert_called_once_with(mock_handle)

    def test_next_raises_stop_iteration_on_empty_data(self):
        mock_lc = Mock(spec=LibConfsecBase)
        mock_response = Mock(spec=Response)
        mock_handle = Mock(spec=ResponseStreamHandle)
        mock_lc.response_stream_get_next.return_value = b""

        stream = ResponseStream(mock_lc, mock_response, mock_handle)

        with pytest.raises(StopIteration):
            next(stream)

    def test_for_loop_iteration(self):
        mock_lc = Mock(spec=LibConfsecBase)
        mock_response = Mock(spec=Response)
        mock_handle = Mock(spec=ResponseStreamHandle)

        # Simulate streaming data then ending
        mock_lc.response_stream_get_next.side_effect = [
            b"chunk1",
            b"chunk2",
            b"chunk3",
            b"",  # End of stream
        ]

        stream = ResponseStream(mock_lc, mock_response, mock_handle)
        chunks = list(stream)

        assert chunks == [b"chunk1", b"chunk2", b"chunk3"]
        assert mock_lc.response_stream_get_next.call_count == 4

    def test_get_next_returns_bytes_from_libconfsec(self):
        mock_lc = Mock(spec=LibConfsecBase)
        mock_response = Mock(spec=Response)
        mock_handle = Mock(spec=ResponseStreamHandle)
        mock_lc.response_stream_get_next.return_value = b"some data"

        stream = ResponseStream(mock_lc, mock_response, mock_handle)
        result = stream.get_next()

        assert result == b"some data"
        mock_lc.response_stream_get_next.assert_called_once_with(mock_handle)

    def test_close_calls_response_stream_destroy(self):
        mock_lc = Mock(spec=LibConfsecBase)
        mock_response = Mock(spec=Response)
        mock_handle = Mock(spec=ResponseStreamHandle)

        stream = ResponseStream(mock_lc, mock_response, mock_handle)
        stream.close()

        mock_lc.response_stream_destroy.assert_called_once_with(mock_handle)

    def test_close_releases_response_reference(self):
        mock_lc = Mock(spec=LibConfsecBase)
        mock_response = Mock(spec=Response)
        mock_handle = Mock(spec=ResponseStreamHandle)

        stream = ResponseStream(mock_lc, mock_response, mock_handle)
        assert stream._resp is mock_response

        stream.close()

        assert stream._resp is None

    def test_context_manager_calls_close(self):
        mock_lc = Mock(spec=LibConfsecBase)
        mock_response = Mock(spec=Response)
        mock_handle = Mock(spec=ResponseStreamHandle)

        with ResponseStream(mock_lc, mock_response, mock_handle) as _:
            pass

        mock_lc.response_stream_destroy.assert_called_once_with(mock_handle)

    def test_response_reference_keeps_response_alive(self):
        mock_lc = Mock(spec=LibConfsecBase)
        mock_response = Mock(spec=Response)
        mock_handle = Mock(spec=ResponseStreamHandle)

        stream = ResponseStream(mock_lc, mock_response, mock_handle)

        # Verify the response reference is held
        assert stream._resp is mock_response

        # Simulate losing the original response reference
        mock_response = None

        # Stream should still hold the reference
        assert stream._resp is not None
