"""
Tests for the AI event-summary service.
The Gemini HTTP call is mocked — no network, no API key needed.
"""
import httpx2
import pytest

from app.services import ai_service


@pytest.fixture(autouse=True)
def _no_retry_backoff(monkeypatch):
    # Keep retry tests instant — no real sleeping.
    monkeypatch.setattr(ai_service, "RETRY_BACKOFF_SECONDS", 0)


class TestBuildEventPrompt:
    def test_includes_title(self):
        prompt = ai_service.build_event_prompt({"title": "Jazz Night"})
        assert "Jazz Night" in prompt

    def test_free_event_shows_free_entry(self):
        prompt = ai_service.build_event_prompt({"title": "X", "price_cents": 0})
        assert "Free entry" in prompt

    def test_paid_event_shows_price(self):
        prompt = ai_service.build_event_prompt({"title": "X", "price_cents": 1500})
        assert "£15.00" in prompt

    def test_discount_is_flagged(self):
        prompt = ai_service.build_event_prompt(
            {"title": "X", "price_cents": 1000, "original_price_cents": 2000}
        )
        assert "discounted from £20.00" in prompt

    def test_venue_with_address(self):
        prompt = ai_service.build_event_prompt(
            {"title": "X", "venue_name": "The Roundhouse", "venue_address": "Camden"}
        )
        assert "The Roundhouse, Camden" in prompt

    def test_omits_missing_optional_fields(self):
        prompt = ai_service.build_event_prompt({"title": "X"})
        assert "Category:" not in prompt
        assert "Venue:" not in prompt


class _FakeResponse:
    def __init__(self, payload, status_ok=True):
        self._payload = payload
        self.status_code = 200 if status_ok else 400
        self.text = "" if status_ok else '{"error": {"message": "bad request"}}'

    def json(self):
        return self._payload


def _gemini_payload(text: str) -> dict:
    return {"candidates": [{"content": {"parts": [{"text": text}]}}]}


class TestGenerateEventSummary:
    def test_returns_none_without_api_key(self, monkeypatch):
        monkeypatch.setattr(ai_service, "GEMINI_API_KEY", "")
        result = ai_service.generate_event_summary({"title": "X"})
        assert result is None

    def test_returns_summary_on_success(self, monkeypatch):
        monkeypatch.setattr(ai_service, "GEMINI_API_KEY", "fake-key")

        def fake_post(*args, **kwargs):
            return _FakeResponse(_gemini_payload("  A lively jazz night in Camden.  "))

        monkeypatch.setattr(ai_service.httpx2, "post", fake_post)

        result = ai_service.generate_event_summary({"title": "Jazz Night"})
        assert result == "A lively jazz night in Camden."

    def test_returns_none_on_network_error(self, monkeypatch):
        monkeypatch.setattr(ai_service, "GEMINI_API_KEY", "fake-key")

        def fake_post(*args, **kwargs):
            raise httpx2.ConnectError("boom")

        monkeypatch.setattr(ai_service.httpx2, "post", fake_post)

        result = ai_service.generate_event_summary({"title": "X"})
        assert result is None

    def test_returns_none_on_malformed_response(self, monkeypatch):
        monkeypatch.setattr(ai_service, "GEMINI_API_KEY", "fake-key")

        def fake_post(*args, **kwargs):
            return _FakeResponse({"unexpected": "shape"})

        monkeypatch.setattr(ai_service.httpx2, "post", fake_post)

        result = ai_service.generate_event_summary({"title": "X"})
        assert result is None

    def test_returns_none_on_http_error_status(self, monkeypatch):
        monkeypatch.setattr(ai_service, "GEMINI_API_KEY", "fake-key")

        def fake_post(*args, **kwargs):
            return _FakeResponse(_gemini_payload("ignored"), status_ok=False)

        monkeypatch.setattr(ai_service.httpx2, "post", fake_post)

        result = ai_service.generate_event_summary({"title": "X"})
        assert result is None
