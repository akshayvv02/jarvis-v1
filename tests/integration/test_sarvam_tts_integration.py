from __future__ import annotations

import os
from pathlib import Path
import wave

import pytest

from jarvis.tts import SarvamTTS, TTSRequest


@pytest.mark.integration
def test_sarvam_tts_real_api(tmp_path: Path) -> None:
    if os.getenv("SARVAM_INTEGRATION_TESTS") != "true":
        pytest.skip("Set SARVAM_INTEGRATION_TESTS=true to run real Sarvam tests")

    api_key = os.getenv("SARVAM_API_KEY")
    if not api_key:
        pytest.skip("SARVAM_API_KEY is required")

    tts = SarvamTTS(
        api_key=api_key,
        model=os.getenv("SARVAM_TTS_MODEL", "bulbul:v3"),
        speaker=os.getenv("SARVAM_TTS_SPEAKER", "priya"),
        pace=float(os.getenv("SARVAM_TTS_PACE", "1.0")),
        output_format=os.getenv("SARVAM_TTS_OUTPUT_FORMAT", "wav"),
        timeout_seconds=30,
    )

    audio = tts.synthesize(
        TTSRequest(text="Hello Akshay, Jarvis is online.", language_code="en-IN")
    )
    path = tmp_path / "tts.wav"
    path.write_bytes(audio.audio_bytes)

    assert path.stat().st_size > 44
    with wave.open(str(path), "rb") as wav:
        assert wav.getnframes() > 0
        assert wav.getframerate() > 0
