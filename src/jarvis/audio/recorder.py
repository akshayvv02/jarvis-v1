from __future__ import annotations

from dataclasses import dataclass
import logging
from pathlib import Path
import tempfile
from typing import Callable
import uuid
import wave

import numpy as np

from jarvis.audio.interface import AudioChunk, AudioInput

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RecordedAudio:
    path: Path
    sample_rate: int
    channels: int
    duration_seconds: float


@dataclass(frozen=True)
class QueryRecorderConfig:
    max_duration_seconds: float
    silence_duration_ms: int
    speech_start_threshold: float
    no_speech_timeout_seconds: float
    temp_dir: Path


class QueryRecorder:
    def __init__(self, *, audio_input: AudioInput, config: QueryRecorderConfig) -> None:
        self._audio_input = audio_input
        self._config = config

    def record(self, should_continue: Callable[[], bool] | None = None) -> RecordedAudio | None:
        should_continue = should_continue or (lambda: True)
        self._config.temp_dir.mkdir(parents=True, exist_ok=True)
        logger.info("Listening for query speech")

        chunks: list[AudioChunk] = []
        speech_started = False
        speech_elapsed = 0.0
        total_elapsed = 0.0
        silence_elapsed_ms = 0.0

        while should_continue() and total_elapsed < self._config.no_speech_timeout_seconds:
            chunk = self._audio_input.read()
            chunk_duration = len(chunk.samples) / chunk.sample_rate
            total_elapsed += chunk_duration

            if _rms(chunk.samples) >= self._config.speech_start_threshold:
                speech_started = True
                chunks.append(chunk)
                speech_elapsed += chunk_duration
                break

        if not speech_started:
            if not should_continue():
                logger.info("Query recording interrupted before speech started")
                return None
            logger.info(
                "No query speech detected before timeout: timeout_seconds=%.2f",
                self._config.no_speech_timeout_seconds,
            )
            return None

        logger.info("Query speech started")
        while should_continue() and speech_elapsed < self._config.max_duration_seconds:
            chunk = self._audio_input.read()
            chunks.append(chunk)
            chunk_duration = len(chunk.samples) / chunk.sample_rate
            speech_elapsed += chunk_duration

            if _rms(chunk.samples) >= self._config.speech_start_threshold:
                silence_elapsed_ms = 0.0
            else:
                silence_elapsed_ms += chunk_duration * 1000
                if silence_elapsed_ms >= self._config.silence_duration_ms:
                    break

        if not should_continue():
            logger.info("Query recording interrupted")
            return None

        recorded = _write_recording(chunks, self._config.temp_dir)
        logger.info(
            "Query recorded: path=%s duration_seconds=%.2f",
            recorded.path,
            recorded.duration_seconds,
        )
        return recorded


def _rms(samples: np.ndarray) -> float:
    if len(samples) == 0:
        return 0.0
    return float(np.sqrt(np.mean(samples.astype(np.float32) ** 2)))


def _write_recording(chunks: list[AudioChunk], temp_dir: Path) -> RecordedAudio:
    if not chunks:
        raise ValueError("Cannot write empty recording")

    sample_rate = chunks[0].sample_rate
    channels = chunks[0].channels
    samples = np.concatenate([chunk.samples for chunk in chunks]).astype(np.int16)
    path = temp_dir / f"query-{uuid.uuid4()}.wav"

    with tempfile.NamedTemporaryFile(dir=temp_dir, suffix=".wav", delete=False) as file:
        temp_path = Path(file.name)

    with wave.open(str(temp_path), "wb") as wav:
        wav.setnchannels(channels)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(samples.tobytes())

    temp_path.replace(path)
    return RecordedAudio(
        path=path,
        sample_rate=sample_rate,
        channels=channels,
        duration_seconds=len(samples) / sample_rate,
    )
