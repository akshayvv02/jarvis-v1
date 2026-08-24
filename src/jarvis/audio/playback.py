from __future__ import annotations

import logging
from pathlib import Path
import wave

import numpy as np
import sounddevice as sd

from jarvis.config import AudioDevice

logger = logging.getLogger(__name__)


class SoundDeviceAudioOutput:
    def __init__(self, *, device: AudioDevice = None) -> None:
        self._device = device

    def play(self, audio_file: Path) -> None:
        try:
            samples, sample_rate = _read_wav(audio_file)
            sd.play(samples, samplerate=sample_rate, device=self._device)
            sd.wait()
        except Exception:
            logger.exception("Audio acknowledgement playback failed")
            raise

        logger.info("Acknowledgement played: %s", audio_file)


def _read_wav(audio_file: Path) -> tuple[np.ndarray, int]:
    with wave.open(str(audio_file), "rb") as wav:
        channels = wav.getnchannels()
        sample_width = wav.getsampwidth()
        sample_rate = wav.getframerate()
        frames = wav.readframes(wav.getnframes())

    if sample_width != 2:
        raise ValueError(f"Only 16-bit WAV files are supported: {audio_file}")

    samples = np.frombuffer(frames, dtype=np.int16)
    if channels > 1:
        samples = samples.reshape(-1, channels).mean(axis=1).astype(np.int16)

    return samples, sample_rate
