from __future__ import annotations

from pathlib import Path
import wave

import pytest
import requests

from jarvis.audio.recorder import RecordedAudio
from jarvis.stt.sarvam import SarvamSTT, STTError


class FakeResponse:
    def __init__(self, status_code: int, payload: dict | None = None, text: str = "") -> None:
        self.status_code = status_code
        self._payload = payload
        self.text = text

    def json(self) -> dict:
        if self._payload is None:
            raise ValueError("bad json")
        return self._payload


def test_sarvam_transcript_success(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    audio = _recorded_audio(tmp_path)

    def fake_post(*args: object, **kwargs: object) -> FakeResponse:
        return FakeResponse(
            200,
            {
                "request_id": "request-1",
                "transcript": "haan bhai",
                "language_code": "hi-IN",
            },
        )

    monkeypatch.setattr("jarvis.stt.sarvam.requests.post", fake_post)

    stt = SarvamSTT(
        api_key="test-key",
        model="saaras:v3",
        mode="transcribe",
        language_code="unknown",
        timeout_seconds=10,
    )

    transcript = stt.transcribe(audio)

    assert transcript.text == "haan bhai"
    assert transcript.language_code == "hi-IN"
    assert transcript.request_id == "request-1"


def test_sarvam_requires_api_key() -> None:
    with pytest.raises(ValueError, match="SARVAM_API_KEY"):
        SarvamSTT(
            api_key="",
            model="saaras:v3",
            mode="transcribe",
            language_code="unknown",
            timeout_seconds=10,
        )


@pytest.mark.parametrize(
    ("status_code", "message"),
    [
        (403, "authentication"),
        (429, "rate limit"),
        (422, "rejected audio"),
        (500, "request failed"),
    ],
)
def test_sarvam_http_errors(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    status_code: int,
    message: str,
) -> None:
    audio = _recorded_audio(tmp_path)
    monkeypatch.setattr(
        "jarvis.stt.sarvam.requests.post",
        lambda *args, **kwargs: FakeResponse(status_code, text="problem"),
    )
    stt = _stt()

    with pytest.raises(STTError, match=message):
        stt.transcribe(audio)


def test_sarvam_timeout(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    audio = _recorded_audio(tmp_path)

    def fake_post(*args: object, **kwargs: object) -> FakeResponse:
        raise requests.Timeout

    monkeypatch.setattr("jarvis.stt.sarvam.requests.post", fake_post)

    with pytest.raises(STTError, match="timed out"):
        _stt().transcribe(audio)


def test_sarvam_invalid_response(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    audio = _recorded_audio(tmp_path)
    monkeypatch.setattr(
        "jarvis.stt.sarvam.requests.post",
        lambda *args, **kwargs: FakeResponse(200, {"language_code": "hi-IN"}),
    )

    with pytest.raises(STTError, match="transcript"):
        _stt().transcribe(audio)


def _stt() -> SarvamSTT:
    return SarvamSTT(
        api_key="test-key",
        model="saaras:v3",
        mode="transcribe",
        language_code="unknown",
        timeout_seconds=10,
    )


def _recorded_audio(tmp_path: Path) -> RecordedAudio:
    path = tmp_path / "query.wav"
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(16_000)
        wav.writeframes(b"\x00\x00" * 1280)

    return RecordedAudio(
        path=path,
        sample_rate=16_000,
        channels=1,
        duration_seconds=0.08,
    )
