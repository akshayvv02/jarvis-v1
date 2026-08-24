from __future__ import annotations

import os
from pathlib import Path

import pytest

from jarvis.audio.recorder import RecordedAudio
from jarvis.stt.sarvam import SarvamSTT


@pytest.mark.integration
def test_sarvam_stt_real_api() -> None:
    if os.getenv("SARVAM_INTEGRATION_TESTS") != "true":
        pytest.skip("Set SARVAM_INTEGRATION_TESTS=true to run real Sarvam tests")

    api_key = os.getenv("SARVAM_API_KEY")
    audio_path = os.getenv("SARVAM_TEST_AUDIO_PATH")
    if not api_key or not audio_path:
        pytest.skip("Set SARVAM_API_KEY and SARVAM_TEST_AUDIO_PATH")

    path = Path(audio_path)
    stt = SarvamSTT(
        api_key=api_key,
        model=os.getenv("SARVAM_STT_MODEL", "saaras:v3"),
        mode=os.getenv("SARVAM_STT_MODE", "transcribe"),
        language_code=os.getenv("SARVAM_STT_LANGUAGE_CODE", "unknown"),
        timeout_seconds=30,
    )

    transcript = stt.transcribe(
        RecordedAudio(path=path, sample_rate=16_000, channels=1, duration_seconds=0)
    )

    assert transcript.text
