from __future__ import annotations

from pathlib import Path
import wave

import numpy as np

from jarvis.audio.interface import AudioChunk
from jarvis.audio.recorder import RecordedAudio
from jarvis.config import Settings
from jarvis.llm.models import LLMChunk, LLMRequest
from jarvis.main import AssistantState, JarvisApp
from jarvis.stt.models import Transcript


class FakeAudioInput:
    def __init__(self) -> None:
        self.flush_calls: list[int] = []

    def start(self) -> None:
        pass

    def read(self) -> AudioChunk:
        return AudioChunk(
            samples=np.zeros(1280, dtype=np.int16),
            sample_rate=16_000,
            channels=1,
        )

    def flush(self, duration_ms: int) -> None:
        self.flush_calls.append(duration_ms)

    def stop(self) -> None:
        pass


class FakeAudioOutput:
    def __init__(self) -> None:
        self.played: list[Path] = []

    def play(self, audio_file: Path) -> None:
        self.played.append(audio_file)


class FakeRecorder:
    def __init__(self, recorded_audio: RecordedAudio | None) -> None:
        self.recorded_audio = recorded_audio
        self.calls = 0

    def record(self, should_continue: object = None) -> RecordedAudio | None:
        self.calls += 1
        return self.recorded_audio


class FakeWakeWordDetector:
    def __init__(self) -> None:
        self.process_calls = 0

    def start(self) -> None:
        pass

    def process(self, audio: AudioChunk) -> list[object]:
        self.process_calls += 1
        return []

    def stop(self) -> None:
        pass


class FakeDebouncer:
    pass


class FakeSTT:
    def __init__(self) -> None:
        self.calls = 0

    def transcribe(self, audio: RecordedAudio) -> Transcript:
        self.calls += 1
        return Transcript(text="hello", language_code="en-IN", request_id="request-1")


class FakeLLM:
    def __init__(self) -> None:
        self.requests: list[LLMRequest] = []

    def stream(self, request: LLMRequest) -> object:
        self.requests.append(request)
        yield LLMChunk(text="hi there")


def test_handle_wake_word_runs_phase_2_states(tmp_path: Path) -> None:
    audio_input = FakeAudioInput()
    audio_output = FakeAudioOutput()
    recorded_audio = _recorded_audio(tmp_path)
    recorder = FakeRecorder(recorded_audio)
    wakeword_detector = FakeWakeWordDetector()
    stt = FakeSTT()
    llm = FakeLLM()
    settings = Settings(
        ack_audio_path=tmp_path / "ack.wav",
        audio_flush_duration_ms=123,
        cleanup_query_audio=True,
        sarvam_api_key="test-key",
    )
    app = JarvisApp(
        settings=settings,
        audio_input=audio_input,
        audio_output=audio_output,
        query_recorder=recorder,  # type: ignore[arg-type]
        wakeword_detector=wakeword_detector,
        debouncer=FakeDebouncer(),  # type: ignore[arg-type]
        stt=stt,
        llm=llm,
    )
    app._running = True

    app._handle_wake_word()

    assert app.state == AssistantState.IDLE
    assert audio_output.played == [settings.ack_audio_path]
    assert audio_input.flush_calls == [123, 123]
    assert recorder.calls == 1
    assert stt.calls == 1
    assert [request.user_text for request in llm.requests] == ["hello"]
    assert wakeword_detector.process_calls > 0
    assert not recorded_audio.path.exists()


def _recorded_audio(tmp_path: Path) -> RecordedAudio:
    path = tmp_path / "query.wav"
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(16_000)
        wav.writeframes(b"\x00\x00" * 1280)
    return RecordedAudio(path=path, sample_rate=16_000, channels=1, duration_seconds=0.08)
