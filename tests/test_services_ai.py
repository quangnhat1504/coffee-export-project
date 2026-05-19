"""Unit tests for app.services.ai_service module.

Tests cover:
- AI config check (has_ai_config=False → 503)
- Successful JSON response extraction
- SSE streaming response parsing
- Empty SSE stream error handling
- Network errors (ConnectionError, Timeout)
- Unexpected response structure (KeyError/IndexError)
- Missing/empty question uses default Vietnamese string

Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7
"""

from __future__ import annotations

import json

import responses
from requests.exceptions import ConnectionError, Timeout

from app.config import Settings
from app.services.ai_service import create_insight


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_settings(has_ai: bool = True) -> Settings:
    """Create a Settings instance with or without AI config."""
    return Settings(
        db_host="localhost",
        db_port="3306",
        db_user="test",
        db_password="test",
        db_name="testdb",
        db_ca_cert=None,
        ai_base_url="http://localhost:9999/v1",
        ai_api_key="test-key" if has_ai else None,
        ai_model="test-model",
        flask_host="127.0.0.1",
        flask_port=5000,
        debug=False,
    )


AI_URL = "http://localhost:9999/v1/chat/completions"


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestCreateInsightNoConfig:
    """Requirement 7.1: has_ai_config=False returns 503."""

    def test_no_ai_config_returns_503(self):
        settings = _make_settings(has_ai=False)
        result = create_insight(settings, {"question": "test?"})

        assert result["success"] is False
        assert result["status_code"] == 503
        assert "not configured" in result["error"]


class TestCreateInsightJsonResponse:
    """Requirement 7.2: Successful JSON response extracts choices[0].message.content."""

    @responses.activate
    def test_successful_json_response(self):
        body = {
            "choices": [
                {"message": {"content": "Đây là phân tích dữ liệu cà phê."}}
            ]
        }
        responses.add(
            responses.POST,
            AI_URL,
            json=body,
            status=200,
            content_type="application/json",
        )

        settings = _make_settings(has_ai=True)
        result = create_insight(settings, {"question": "Phân tích?", "data": {"x": 1}})

        assert result["success"] is True
        assert result["model"] == "test-model"
        assert result["insight"] == "Đây là phân tích dữ liệu cà phê."


class TestCreateInsightSSEStreaming:
    """Requirement 7.3: SSE streaming response parsing."""

    @responses.activate
    def test_sse_streaming_concatenates_delta_content(self):
        sse_lines = [
            f"data: {json.dumps({'choices': [{'delta': {'content': 'Hello'}}]})}",
            f"data: {json.dumps({'choices': [{'delta': {'content': ' world'}}]})}",
            "data: [DONE]",
        ]
        sse_body = "\n".join(sse_lines)

        responses.add(
            responses.POST,
            AI_URL,
            body=sse_body,
            status=200,
            content_type="text/event-stream",
        )

        settings = _make_settings(has_ai=True)
        result = create_insight(settings, {"question": "Test?"})

        assert result["success"] is True
        assert result["insight"] == "Hello world"

    @responses.activate
    def test_sse_streaming_with_message_content(self):
        """SSE with message.content instead of delta.content."""
        sse_lines = [
            f"data: {json.dumps({'choices': [{'message': {'content': 'Part1'}}]})}",
            f"data: {json.dumps({'choices': [{'message': {'content': 'Part2'}}]})}",
            "data: [DONE]",
        ]
        sse_body = "\n".join(sse_lines)

        responses.add(
            responses.POST,
            AI_URL,
            body=sse_body,
            status=200,
            content_type="text/event-stream",
        )

        settings = _make_settings(has_ai=True)
        result = create_insight(settings, {"question": "Test?"})

        assert result["success"] is True
        assert result["insight"] == "Part1Part2"


class TestCreateInsightEmptySSE:
    """Requirement 7.4: Empty SSE stream returns success=False, status_code=502."""

    @responses.activate
    def test_empty_sse_stream(self):
        # SSE with no data lines containing content
        sse_body = "data: [DONE]\n"

        responses.add(
            responses.POST,
            AI_URL,
            body=sse_body,
            status=200,
            content_type="text/event-stream",
        )

        settings = _make_settings(has_ai=True)
        result = create_insight(settings, {"question": "Test?"})

        assert result["success"] is False
        assert result["status_code"] == 502
        assert "response_preview" in result

    @responses.activate
    def test_sse_with_only_non_content_events(self):
        """SSE lines that have no delta.content or message.content."""
        sse_lines = [
            f"data: {json.dumps({'choices': [{'delta': {'role': 'assistant'}}]})}",
            "data: [DONE]",
        ]
        sse_body = "\n".join(sse_lines)

        responses.add(
            responses.POST,
            AI_URL,
            body=sse_body,
            status=200,
            content_type="text/event-stream",
        )

        settings = _make_settings(has_ai=True)
        result = create_insight(settings, {"question": "Test?"})

        assert result["success"] is False
        assert result["status_code"] == 502
        assert "response_preview" in result


class TestCreateInsightNetworkErrors:
    """Requirement 7.5: Network errors return success=False, status_code=502."""

    @responses.activate
    def test_connection_error(self):
        responses.add(
            responses.POST,
            AI_URL,
            body=ConnectionError("Connection refused"),
        )

        settings = _make_settings(has_ai=True)
        result = create_insight(settings, {"question": "Test?"})

        assert result["success"] is False
        assert result["status_code"] == 502
        assert "AI request failed" in result["error"]

    @responses.activate
    def test_timeout_error(self):
        responses.add(
            responses.POST,
            AI_URL,
            body=Timeout("Request timed out"),
        )

        settings = _make_settings(has_ai=True)
        result = create_insight(settings, {"question": "Test?"})

        assert result["success"] is False
        assert result["status_code"] == 502
        assert "AI request failed" in result["error"]


class TestCreateInsightUnexpectedStructure:
    """Requirement 7.6: Unexpected response structure returns 502 with response_preview."""

    @responses.activate
    def test_missing_choices_key(self):
        """JSON response without 'choices' key triggers KeyError."""
        body = {"result": "something unexpected"}
        responses.add(
            responses.POST,
            AI_URL,
            json=body,
            status=200,
            content_type="application/json",
        )

        settings = _make_settings(has_ai=True)
        result = create_insight(settings, {"question": "Test?"})

        assert result["success"] is False
        assert result["status_code"] == 502
        assert "response_preview" in result

    @responses.activate
    def test_empty_choices_list(self):
        """JSON response with empty choices list triggers IndexError."""
        body = {"choices": []}
        responses.add(
            responses.POST,
            AI_URL,
            json=body,
            status=200,
            content_type="application/json",
        )

        settings = _make_settings(has_ai=True)
        result = create_insight(settings, {"question": "Test?"})

        assert result["success"] is False
        assert result["status_code"] == 502
        assert "response_preview" in result


class TestCreateInsightDefaultQuestion:
    """Requirement 7.7: Missing/empty question uses default Vietnamese string."""

    @responses.activate
    def test_missing_question_key(self):
        body = {
            "choices": [
                {"message": {"content": "Phân tích mặc định."}}
            ]
        }
        responses.add(
            responses.POST,
            AI_URL,
            json=body,
            status=200,
            content_type="application/json",
        )

        settings = _make_settings(has_ai=True)
        result = create_insight(settings, {"data": {"x": 1}})

        assert result["success"] is True
        # Verify the request used the default question
        request_body = json.loads(responses.calls[0].request.body)
        user_msg = request_body["messages"][1]["content"]
        assert "Hãy phân tích ngắn gọn dữ liệu cà phê này." in user_msg

    @responses.activate
    def test_empty_question_string(self):
        body = {
            "choices": [
                {"message": {"content": "Phân tích mặc định."}}
            ]
        }
        responses.add(
            responses.POST,
            AI_URL,
            json=body,
            status=200,
            content_type="application/json",
        )

        settings = _make_settings(has_ai=True)
        result = create_insight(settings, {"question": "", "data": {"x": 1}})

        assert result["success"] is True
        request_body = json.loads(responses.calls[0].request.body)
        user_msg = request_body["messages"][1]["content"]
        assert "Hãy phân tích ngắn gọn dữ liệu cà phê này." in user_msg

    @responses.activate
    def test_none_question(self):
        body = {
            "choices": [
                {"message": {"content": "Phân tích mặc định."}}
            ]
        }
        responses.add(
            responses.POST,
            AI_URL,
            json=body,
            status=200,
            content_type="application/json",
        )

        settings = _make_settings(has_ai=True)
        result = create_insight(settings, {"question": None, "data": {}})

        assert result["success"] is True
        request_body = json.loads(responses.calls[0].request.body)
        user_msg = request_body["messages"][1]["content"]
        assert "Hãy phân tích ngắn gọn dữ liệu cà phê này." in user_msg


# ---------------------------------------------------------------------------
# Property-Based Tests
# ---------------------------------------------------------------------------

import pytest
from hypothesis import given, strategies as st, assume, settings as hyp_settings

from app.services.ai_service import _extract_content


class TestPropertySSEStreamParsing:
    """Property 11: AI SSE stream parsing and concatenation.

    For any sequence of valid SSE data lines containing delta.content fields,
    _extract_content SHALL concatenate all content values in order.

    **Validates: Requirements 7.3**
    """

    # Feature: unit-tests, Property 11: AI SSE stream parsing and concatenation

    @pytest.mark.property
    @hyp_settings(max_examples=100)
    @given(
        chunks=st.lists(
            st.text(min_size=1, max_size=50, alphabet=st.characters(
                blacklist_categories=("Cs",),  # exclude surrogates
                blacklist_characters=("\x00", "\\", '"'),  # avoid JSON-breaking chars
            )),
            min_size=1,
            max_size=10,
        )
    )
    def test_sse_stream_concatenates_delta_content_in_order(self, chunks):
        """Generated SSE delta.content chunks are concatenated in order."""
        import requests.models

        assume(any(len(c.strip()) > 0 for c in chunks))

        # Build SSE body from generated chunks
        sse_lines = []
        for chunk in chunks:
            event = {"choices": [{"delta": {"content": chunk}}]}
            sse_lines.append(f"data: {json.dumps(event)}")
        sse_lines.append("data: [DONE]")
        sse_body = "\n".join(sse_lines)

        # Create a mock response object with text/event-stream content type
        mock_response = requests.models.Response()
        mock_response.status_code = 200
        mock_response.headers["content-type"] = "text/event-stream"
        mock_response._content = sse_body.encode("utf-8")
        mock_response.encoding = "utf-8"

        result = _extract_content(mock_response)

        expected = "".join(chunks)
        assert result == expected


# ---------------------------------------------------------------------------
# Property-Based Tests
# ---------------------------------------------------------------------------

import pytest
from hypothesis import given, settings as hyp_settings, strategies as st
from unittest.mock import MagicMock

from app.services.ai_service import _extract_content


class TestPropertyAIJsonContentExtraction:
    """Property 10: AI JSON response content extraction.

    For any valid JSON response body conforming to the OpenAI chat completions
    format (with choices[0].message.content present), _extract_content SHALL
    return the exact content string from that path.

    **Validates: Requirements 7.2**
    """

    @pytest.mark.property
    @hyp_settings(max_examples=100)
    @given(content=st.text(min_size=1, max_size=500))
    def test_extract_content_returns_exact_content_string(self, content: str):
        """Feature: unit-tests, Property 10: AI JSON response content extraction"""
        # Build a mock requests.Response with JSON body
        body = {"choices": [{"message": {"content": content}}]}

        mock_response = MagicMock()
        mock_response.headers = {"content-type": "application/json"}
        mock_response.json.return_value = body

        result = _extract_content(mock_response)

        assert result == content
