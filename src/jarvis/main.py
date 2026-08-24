from __future__ import annotations

from enum import Enum
import logging
from pathlib import Path
import signal
import time

import numpy as np

from jarvis.audio import AudioInput, AudioOutput
from jarvis.audio.interface import AudioChunk
from jarvis.audio.microphone import SoundDeviceMicrophone
from jarvis.audio.playback import SoundDeviceAudioOutput
from jarvis.audio.recorder import QueryRecorder, QueryRecorderConfig
from jarvis.config import Settings
from jarvis.logging_config import configure_logging
from jarvis.stt import SarvamSTT, SpeechToText, STTError
from jarvis.wakeword import OpenWakeWordDetector, WakeWordDebouncer, WakeWordDetector

logger = logging.getLogger(__name__)


class AssistantState(Enum):
    IDLE = "idle"
    ACKNOWLEDGING = "acknowledging"
    LISTENING = "listening"
    TRANSCRIBING = "transcribing"


class JarvisApp:
    def __init__(
        self,
        *,
        settings: Settings,
        audio_input: AudioInput,
        audio_output: AudioOutput,
        query_recorder: QueryRecorder,
        wakeword_detector: WakeWordDetector,
        debouncer: WakeWordDebouncer,
        stt: SpeechToText,
    ) -> None:
        self._settings = settings
        self._audio_input = audio_input
        self._audio_output = audio_output
        self._query_recorder = query_recorder
        self._wakeword_detector = wakeword_detector
        self._debouncer = debouncer
        self._stt = stt
        self._state = AssistantState.IDLE
        self._running = False
        self._ignore_wake_until = 0.0

    def request_shutdown(self, signum: int, _frame: object) -> None:
        logger.info("Shutdown requested: signal=%s", signum)
        self._running = False

    @property
    def state(self) -> AssistantState:
        return self._state

    def run(self) -> int:
        logger.info("Jarvis starting")
        try:
            self._wakeword_detector.start()
            self._audio_input.start()
            self._running = True

            self._transition(AssistantState.IDLE)
            logger.info('Listening for "Hey Jarvis"...')
            while self._running:
                chunk = self._audio_input.read()
                if time.monotonic() < self._ignore_wake_until:
                    continue

                detections = self._wakeword_detector.process(chunk)
                now = time.monotonic()

                for detection in detections:
                    allowed = self._debouncer.allow(detection, now)
                    if allowed is not None:
                        logger.info(
                            "WAKE WORD DETECTED: %s score=%.3f",
                            allowed.name,
                            allowed.score,
                        )
                        self._handle_wake_word()
                        if self._running:
                            logger.info('Listening for "Hey Jarvis"...')
        finally:
            self._audio_input.stop()
            self._wakeword_detector.stop()
            logger.info("Jarvis stopped")

        return 0

    def _handle_wake_word(self) -> None:
        self._transition(AssistantState.ACKNOWLEDGING)
        self._audio_output.play(self._settings.ack_audio_path)

        self._audio_input.flush(self._settings.audio_flush_duration_ms)

        self._transition(AssistantState.LISTENING)
        recorded_audio = self._query_recorder.record(should_continue=lambda: self._running)
        if recorded_audio is None:
            self._finish_interaction()
            return

        self._transition(AssistantState.TRANSCRIBING)
        try:
            if self._running:
                transcript = self._stt.transcribe(recorded_audio)
                logger.info('You said: "%s"', transcript.text)
                if transcript.language_code:
                    logger.info("Language: %s", transcript.language_code)
                if transcript.request_id:
                    logger.info("STT request: %s", transcript.request_id)
        except STTError:
            logger.exception("Transcription failed")
        finally:
            if self._settings.cleanup_query_audio:
                _cleanup_recording(recorded_audio.path)
            self._finish_interaction()

    def _finish_interaction(self) -> None:
        if self._running:
            self._resume_wake_detection()
        else:
            self._transition(AssistantState.IDLE)

    def _resume_wake_detection(self) -> None:
        self._audio_input.flush(self._settings.audio_flush_duration_ms)
        self._clear_wakeword_context()
        self._ignore_wake_until = (
            time.monotonic() + self._settings.wakeword_resume_delay_ms / 1000
        )
        self._transition(AssistantState.IDLE)

    def _clear_wakeword_context(self) -> None:
        if self._settings.wakeword_reset_duration_ms <= 0:
            return

        chunks = max(
            1,
            round(
                (self._settings.wakeword_reset_duration_ms / 1000)
                * self._settings.sample_rate
                / self._settings.chunk_size
            ),
        )
        silence = np.zeros(self._settings.chunk_size, dtype=np.int16)
        for _ in range(chunks):
            self._wakeword_detector.process(
                AudioChunk(
                    samples=silence,
                    sample_rate=self._settings.sample_rate,
                    channels=self._settings.channels,
                )
            )
        logger.info(
            "Wake-word context cleared: duration_ms=%s",
            self._settings.wakeword_reset_duration_ms,
        )

    def _transition(self, state: AssistantState) -> None:
        self._state = state
        logger.info("Assistant state: %s", state.value)


def build_app(settings: Settings) -> JarvisApp:
    audio_input = SoundDeviceMicrophone(
        device=settings.audio_device,
        sample_rate=settings.sample_rate,
        channels=settings.channels,
        chunk_size=settings.chunk_size,
    )
    audio_output = SoundDeviceAudioOutput(device=settings.audio_output_device)
    query_recorder = QueryRecorder(
        audio_input=audio_input,
        config=QueryRecorderConfig(
            max_duration_seconds=settings.query_max_duration_seconds,
            silence_duration_ms=settings.silence_duration_ms,
            speech_start_threshold=settings.speech_start_threshold,
            no_speech_timeout_seconds=settings.query_no_speech_timeout_seconds,
            temp_dir=settings.query_temp_dir,
        ),
    )
    wakeword_detector = OpenWakeWordDetector(
        model_name=settings.wakeword_model,
        threshold=settings.wakeword_threshold,
    )
    debouncer = WakeWordDebouncer(cooldown_ms=settings.wakeword_cooldown_ms)
    stt = SarvamSTT(
        api_key=settings.sarvam_api_key or "",
        model=settings.sarvam_stt_model,
        mode=settings.sarvam_stt_mode,
        language_code=settings.sarvam_stt_language_code,
        timeout_seconds=settings.sarvam_stt_timeout_seconds,
    )
    return JarvisApp(
        settings=settings,
        audio_input=audio_input,
        audio_output=audio_output,
        query_recorder=query_recorder,
        wakeword_detector=wakeword_detector,
        debouncer=debouncer,
        stt=stt,
    )


def main() -> int:
    settings = Settings.from_env()
    configure_logging(settings.log_level)
    app = build_app(settings)

    signal.signal(signal.SIGTERM, app.request_shutdown)
    signal.signal(signal.SIGINT, app.request_shutdown)

    try:
        return app.run()
    except Exception:
        logger.exception("Jarvis exited with an unrecoverable error")
        return 1


def _cleanup_recording(path: Path) -> None:
    try:
        path.unlink(missing_ok=True)
    except OSError:
        logger.exception("Failed to clean up query audio: %s", path)
