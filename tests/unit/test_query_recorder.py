from __future__ import annotations

from pathlib import Path
import wave

import numpy as np

from jarvis.audio.interface import AudioChunk
from jarvis.audio.recorder import QueryRecorder, QueryRecorderConfig


class FakeAudioInput:
    def __init__(self, chunks: list[AudioChunk]) -> None:
        self._chunks = chunks
        self.flush_calls: list[int] = []

    def start(self) -> None:
        pass

    def read(self) -> AudioChunk:
        if self._chunks:
            return self._chunks.pop(0)
        return _chunk(0)

    def flush(self, duration_ms: int) -> None:
        self.flush_calls.append(duration_ms)

    def stop(self) -> None:
        pass


def test_query_recorder_waits_for_speech_and_stops_after_silence(tmp_path: Path) -> None:
    audio = FakeAudioInput(
        [
            _chunk(0),
            _chunk(1200),
            _chunk(1300),
            _chunk(0),
            _chunk(0),
        ]
    )
    recorder = QueryRecorder(audio_input=audio, config=_config(tmp_path))

    recorded = recorder.record()

    assert recorded is not None
    assert recorded.path.exists()
    assert recorded.sample_rate == 16_000
    assert recorded.channels == 1
    with wave.open(str(recorded.path), "rb") as wav:
        assert wav.getframerate() == 16_000
        assert wav.getnchannels() == 1
        assert wav.getsampwidth() == 2


def test_query_recorder_returns_none_when_no_speech_starts(tmp_path: Path) -> None:
    audio = FakeAudioInput([_chunk(0), _chunk(0), _chunk(0)])
    recorder = QueryRecorder(
        audio_input=audio,
        config=QueryRecorderConfig(
            max_duration_seconds=5,
            silence_duration_ms=160,
            speech_start_threshold=500,
            no_speech_timeout_seconds=0.2,
            temp_dir=tmp_path,
        ),
    )

    assert recorder.record() is None


def test_query_recorder_stops_at_max_duration(tmp_path: Path) -> None:
    audio = FakeAudioInput([_chunk(1500) for _ in range(10)])
    recorder = QueryRecorder(
        audio_input=audio,
        config=QueryRecorderConfig(
            max_duration_seconds=0.24,
            silence_duration_ms=1000,
            speech_start_threshold=500,
            no_speech_timeout_seconds=1,
            temp_dir=tmp_path,
        ),
    )

    recorded = recorder.record()

    assert recorded is not None
    assert recorded.duration_seconds >= 0.24


def _config(tmp_path: Path) -> QueryRecorderConfig:
    return QueryRecorderConfig(
        max_duration_seconds=5,
        silence_duration_ms=160,
        speech_start_threshold=500,
        no_speech_timeout_seconds=1,
        temp_dir=tmp_path,
    )


def _chunk(amplitude: int) -> AudioChunk:
    samples = np.full(1280, amplitude, dtype=np.int16)
    return AudioChunk(samples=samples, sample_rate=16_000, channels=1)
