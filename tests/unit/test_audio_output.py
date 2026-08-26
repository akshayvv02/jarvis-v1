from __future__ import annotations

from pathlib import Path
import wave

import numpy as np
import pytest

from jarvis.audio.playback import _read_wav


def test_read_wav_loads_16_bit_mono(tmp_path: Path) -> None:
    path = tmp_path / "audio.wav"
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(16_000)
        wav.writeframes(b"\x01\x00\x02\x00")

    samples, sample_rate = _read_wav(path)

    assert sample_rate == 16_000
    assert samples.dtype == np.int16
    assert samples.tolist() == [1, 2]


def test_read_wav_rejects_non_16_bit_audio(tmp_path: Path) -> None:
    path = tmp_path / "audio.wav"
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(1)
        wav.setframerate(16_000)
        wav.writeframes(b"\x01\x02")

    with pytest.raises(ValueError, match="16-bit"):
        _read_wav(path)
