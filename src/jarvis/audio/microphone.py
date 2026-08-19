from __future__ import annotations

import math
import logging

import numpy as np
from scipy.signal import resample_poly
import sounddevice as sd

from jarvis.audio.interface import AudioChunk

logger = logging.getLogger(__name__)


class SoundDeviceMicrophone:
    def __init__(
        self,
        *,
        device: str | None,
        sample_rate: int,
        channels: int,
        chunk_size: int,
    ) -> None:
        self._device = device
        self._sample_rate = sample_rate
        self._channels = channels
        self._chunk_size = chunk_size
        self._stream_sample_rate = sample_rate
        self._stream_chunk_size = chunk_size
        self._stream: sd.InputStream | None = None

    def start(self) -> None:
        try:
            try:
                self._open_stream(self._sample_rate, self._chunk_size)
            except sd.PortAudioError as exc:
                fallback_rate = self._default_sample_rate()
                if fallback_rate == self._sample_rate:
                    raise

                fallback_chunk_size = max(
                    1,
                    round(self._chunk_size * fallback_rate / self._sample_rate),
                )
                logger.warning(
                    "Audio device rejected sample_rate=%s (%s); retrying with "
                    "device default sample_rate=%s and resampling to %s",
                    self._sample_rate,
                    exc,
                    fallback_rate,
                    self._sample_rate,
                )
                self._open_stream(fallback_rate, fallback_chunk_size)

            self._stream.start()
        except Exception:
            logger.exception("Audio input initialization failed")
            self._stream = None
            raise

        logger.info(
            "Audio input initialized: device=%s stream_sample_rate=%s "
            "target_sample_rate=%s channels=%s stream_chunk_size=%s target_chunk_size=%s",
            self._device or "default",
            self._stream_sample_rate,
            self._sample_rate,
            self._channels,
            self._stream_chunk_size,
            self._chunk_size,
        )

    def read(self) -> AudioChunk:
        if self._stream is None:
            raise RuntimeError("Audio input has not been started")

        data, overflowed = self._stream.read(self._chunk_size)
        if overflowed:
            logger.warning("Audio input overflow detected")

        samples = np.asarray(data, dtype=np.int16).reshape(-1)
        if self._stream_sample_rate != self._sample_rate:
            samples = self._resample(samples)

        return AudioChunk(
            samples=samples,
            sample_rate=self._sample_rate,
            channels=self._channels,
        )

    def stop(self) -> None:
        if self._stream is None:
            return

        try:
            self._stream.stop()
            self._stream.close()
        finally:
            self._stream = None
            logger.info("Audio input stopped")

    def _open_stream(self, sample_rate: int, chunk_size: int) -> None:
        self._stream = sd.InputStream(
            device=self._device,
            samplerate=sample_rate,
            channels=self._channels,
            dtype="int16",
            blocksize=chunk_size,
        )
        self._stream_sample_rate = sample_rate
        self._stream_chunk_size = chunk_size

    def _default_sample_rate(self) -> int:
        device_info = sd.query_devices(self._device, "input")
        return round(float(device_info["default_samplerate"]))

    def _resample(self, samples: np.ndarray) -> np.ndarray:
        divisor = math.gcd(self._stream_sample_rate, self._sample_rate)
        resampled = resample_poly(
            samples.astype(np.float32),
            self._sample_rate // divisor,
            self._stream_sample_rate // divisor,
        )
        return np.clip(np.rint(resampled), -32768, 32767).astype(np.int16)
