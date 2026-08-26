from __future__ import annotations

import base64

import pytest
import requests

from jarvis.tts import SarvamTTS, TTSError, TTSRequest


class FakeResponse:
    def __init__(self, status_code: int, payload: dict | None = None, text: str = "") -> None:
        self.status_code = status_code
        self._payload = payload
        self.text = text

    def json(self) -> dict:
        if self._payload is None:
            raise ValueError("bad json")
        return self._payload


def test_sarvam_tts_success(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[dict] = []
    audio_bytes = b"RIFFfake-wave"

    def fake_post(*args: object, **kwargs: object) -> FakeResponse:
        calls.append(kwargs)
        return FakeResponse(
            200,
            {
                "request_id": "request-1",
                "audios": [base64.b64encode(audio_bytes).decode("ascii")],
            },
        )

    monkeypatch.setattr("jarvis.tts.sarvam.requests.post", fake_post)

    audio = _tts().synthesize(TTSRequest(text="hello", language_code="en-IN"))

    assert audio.audio_bytes == audio_bytes
    assert audio.format == "wav"
    assert audio.request_id == "request-1"
    payload = calls[0]["json"]
    assert payload["model"] == "bulbul:v3"
    assert payload["speaker"] == "priya"
    assert payload["language_code"] == "en-IN"
    assert payload["pace"] == 1.0
    assert payload["output_audio_codec"] == "wav"


def test_sarvam_tts_request_speaker_overrides_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[dict] = []
    monkeypatch.setattr(
        "jarvis.tts.sarvam.requests.post",
        lambda *args, **kwargs: calls.append(kwargs)
        or FakeResponse(
            200,
            {"audios": [base64.b64encode(b"RIFFfake-wave").decode("ascii")]},
        ),
    )

    _tts().synthesize(TTSRequest(text="hello", language_code="hi-IN", speaker="ishita"))

    assert calls[0]["json"]["speaker"] == "ishita"
    assert calls[0]["json"]["language_code"] == "hi-IN"


def test_sarvam_tts_requires_api_key() -> None:
    with pytest.raises(ValueError, match="SARVAM_API_KEY"):
        SarvamTTS(
            api_key="",
            model="bulbul:v3",
            speaker="priya",
            pace=1.0,
            output_format="wav",
            timeout_seconds=10,
        )


@pytest.mark.parametrize(
    ("status_code", "message"),
    [
        (403, "authentication"),
        (429, "rate limit"),
        (422, "rejected"),
        (500, "request failed"),
    ],
)
def test_sarvam_tts_http_errors(
    monkeypatch: pytest.MonkeyPatch,
    status_code: int,
    message: str,
) -> None:
    monkeypatch.setattr(
        "jarvis.tts.sarvam.requests.post",
        lambda *args, **kwargs: FakeResponse(status_code, text="problem"),
    )

    with pytest.raises(TTSError, match=message):
        _tts().synthesize(TTSRequest(text="hello", language_code="en-IN"))


def test_sarvam_tts_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_post(*args: object, **kwargs: object) -> FakeResponse:
        raise requests.Timeout

    monkeypatch.setattr("jarvis.tts.sarvam.requests.post", fake_post)

    with pytest.raises(TTSError, match="timed out"):
        _tts().synthesize(TTSRequest(text="hello", language_code="en-IN"))


def test_sarvam_tts_invalid_response(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "jarvis.tts.sarvam.requests.post",
        lambda *args, **kwargs: FakeResponse(200, {"audios": []}),
    )

    with pytest.raises(TTSError, match="audio"):
        _tts().synthesize(TTSRequest(text="hello", language_code="en-IN"))


def test_sarvam_tts_invalid_base64(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "jarvis.tts.sarvam.requests.post",
        lambda *args, **kwargs: FakeResponse(200, {"audios": ["not base64"]}),
    )

    with pytest.raises(TTSError, match="base64"):
        _tts().synthesize(TTSRequest(text="hello", language_code="en-IN"))


def _tts() -> SarvamTTS:
    return SarvamTTS(
        api_key="test-key",
        model="bulbul:v3",
        speaker="priya",
        pace=1.0,
        output_format="wav",
        timeout_seconds=10,
    )
