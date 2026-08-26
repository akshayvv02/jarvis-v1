from __future__ import annotations

import pytest

from jarvis.llm.gemini import GeminiProvider, LLMError
from jarvis.llm.models import LLMRequest


class FakeResponseChunk:
    def __init__(self, text: str | None) -> None:
        self.text = text


class FakeModels:
    def __init__(self, chunks: list[FakeResponseChunk] | None = None) -> None:
        self.chunks = chunks or []
        self.calls: list[dict[str, object]] = []
        self.error: Exception | None = None

    def generate_content_stream(self, **kwargs: object) -> object:
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return iter(self.chunks)


class FakeClient:
    def __init__(self, models: FakeModels) -> None:
        self.models = models


def test_gemini_provider_streams_text_chunks() -> None:
    models = FakeModels(
        [FakeResponseChunk("hello"), FakeResponseChunk(None), FakeResponseChunk("!")]
    )
    provider = GeminiProvider(
        api_key="key",
        model="gemini-test",
        timeout_seconds=10,
        client=FakeClient(models),
        clock=_clock([1.0, 1.1, 1.4]),
    )

    chunks = list(provider.stream(LLMRequest(user_text="say hi", system_prompt="system")))

    assert [chunk.text for chunk in chunks] == ["hello", "!"]
    assert models.calls[0]["model"] == "gemini-test"
    assert models.calls[0]["contents"] == "say hi"
    assert models.calls[0]["config"] is not None


def test_gemini_provider_rejects_empty_key() -> None:
    with pytest.raises(ValueError, match="GEMINI_API_KEY"):
        GeminiProvider(api_key="", model="gemini-test", timeout_seconds=10)


def test_gemini_provider_raises_when_no_text_is_returned() -> None:
    provider = GeminiProvider(
        api_key="key",
        model="gemini-test",
        timeout_seconds=10,
        client=FakeClient(FakeModels([FakeResponseChunk(None)])),
    )

    with pytest.raises(LLMError, match="no usable response"):
        list(provider.stream(LLMRequest(user_text="say hi")))


def test_gemini_provider_maps_rate_limit_error() -> None:
    models = FakeModels()
    models.error = FakeGoogleError(code=429)
    provider = GeminiProvider(
        api_key="key",
        model="gemini-test",
        timeout_seconds=10,
        client=FakeClient(models),
    )

    with pytest.raises(LLMError, match="rate limit"):
        list(provider.stream(LLMRequest(user_text="say hi")))


def test_gemini_provider_maps_read_timeout() -> None:
    models = FakeModels()
    models.error = FakeReadTimeout("The read operation timed out")
    provider = GeminiProvider(
        api_key="key",
        model="gemini-test",
        timeout_seconds=10,
        client=FakeClient(models),
    )

    with pytest.raises(LLMError, match="timed out"):
        list(provider.stream(LLMRequest(user_text="say hi")))


class FakeGoogleError(Exception):
    def __init__(self, code: int) -> None:
        super().__init__("service rejected request")
        self.code = code


class FakeReadTimeout(Exception):
    pass


def _clock(values: list[float]) -> object:
    iterator = iter(values)

    def now() -> float:
        return next(iterator)

    return now
