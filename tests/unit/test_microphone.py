from __future__ import annotations

import numpy as np

from jarvis.audio.microphone import SoundDeviceMicrophone


def test_resample_converts_native_rate_to_target_rate() -> None:
    microphone = SoundDeviceMicrophone(
        device=None,
        sample_rate=16_000,
        channels=1,
        chunk_size=1_280,
    )
    microphone._stream_sample_rate = 48_000

    native_samples = np.zeros(3_840, dtype=np.int16)

    resampled = microphone._resample(native_samples)

    assert resampled.dtype == np.int16
    assert len(resampled) == 1_280
