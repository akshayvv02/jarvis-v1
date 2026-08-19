from __future__ import annotations

import logging

import numpy as np
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
        self._stream: sd.InputStream | None = None

    def start(self) -> None:
        try:
            self._stream = sd.InputStream(
                device=self._device,
                samplerate=self._sample_rate,
                channels=self._channels,
                dtype="int16",
                blocksize=self._chunk_size,
            )
            self._stream.start()
        except Exception:
            logger.exception("Audio input initialization failed")
            self._stream = None
            raise

        logger.info(
            "Audio input initialized: device=%s sample_rate=%s channels=%s chunk_size=%s",
            self._device or "default",
            self._sample_rate,
            self._channels,
            self._chunk_size,
        )

    def read(self) -> AudioChunk:
        if self._stream is None:
            raise RuntimeError("Audio input has not been started")

        data, overflowed = self._stream.read(self._chunk_size)
        if overflowed:
            logger.warning("Audio input overflow detected")

        samples = np.asarray(data, dtype=np.int16).reshape(-1)
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
