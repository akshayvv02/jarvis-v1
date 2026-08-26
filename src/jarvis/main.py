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
from jarvis.llm import GeminiProvider, LLMError, LLMProvider, LLMRequest
from jarvis.logging_config import configure_logging
from jarvis.personality import (
    JarvisPersonality,
    PersonalityConfig,
    PersonalityProvider,
)
from jarvis.stt import SarvamSTT, SpeechToText, STTError
from jarvis.wakeword import OpenWakeWordDetector, WakeWordDebouncer, WakeWordDetector

logger = logging.getLogger(__name__)


class AssistantState(Enum):
    IDLE = "idle"
    ACKNOWLEDGING = "acknowledging"
    LISTENING = "listening"
    TRANSCRIBING = "transcribing"
    PROCESSING = "processing"


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
        llm: LLMProvider,
        personality: PersonalityProvider,
    ) -> None:
        self._settings = settings
        self._audio_input = audio_input
        self._audio_output = audio_output
        self._query_recorder = query_recorder
        self._wakeword_detector = wakeword_detector
        self._debouncer = debouncer
        self._stt = stt
        self._llm = llm
        self._personality = personality
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
        logger.info(
            "LLM provider: gemini model=%s",
            self._settings.gemini_model,
        )
        logger.info(
            "Personality: %s version=%s humor_level=%s",
            self._personality.name,
            self._personality.version,
            self._personality.humor_level,
        )
        if self._settings.prompt_debug:
            logger.debug(
                "Personality system prompt:\n%s",
                self._personality.system_prompt(),
            )
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
            transcript_text: str | None = None
            if self._running:
                transcript = self._stt.transcribe(recorded_audio)
                transcript_text = transcript.text
                logger.info('You said: "%s"', transcript.text)
                if transcript.language_code:
                    logger.info("Language: %s", transcript.language_code)
                if transcript.request_id:
                    logger.info("STT request: %s", transcript.request_id)
            if self._running and transcript_text:
                self._process_transcript(transcript_text)
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

    def _process_transcript(self, transcript_text: str) -> None:
        self._transition(AssistantState.PROCESSING)
        request = LLMRequest(
            user_text=transcript_text,
            system_prompt=self._personality.system_prompt(),
        )

        try:
            response_parts: list[str] = []
            started = time.perf_counter()
            first_chunk_at: float | None = None
            logger.info("Jarvis response:")
            for chunk in self._llm.stream(request):
                if not self._running:
                    break
                if first_chunk_at is None:
                    first_chunk_at = time.perf_counter()
                    print("Jarvis: ", end="", flush=True)
                response_parts.append(chunk.text)
                print(chunk.text, end="", flush=True)
            print(flush=True)
            if response_parts:
                total_ms = (time.perf_counter() - started) * 1000
                ttft_ms = (
                    None
                    if first_chunk_at is None
                    else (first_chunk_at - started) * 1000
                )
                logger.info(
                    "Jarvis response completed: ttft_ms=%s total_ms=%.1f chars=%s",
                    "n/a" if ttft_ms is None else f"{ttft_ms:.1f}",
                    total_ms,
                    len("".join(response_parts)),
                )
        except LLMError:
            print(flush=True)
            logger.exception("LLM response failed")

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
    llm = GeminiProvider(
        api_key=settings.gemini_api_key or "",
        model=settings.gemini_model,
        timeout_seconds=settings.gemini_request_timeout_seconds,
    )
    personality = JarvisPersonality(
        PersonalityConfig(
            name=settings.personality,
            humor_level=settings.humor_level,
            prompt_debug=settings.prompt_debug,
        )
    )
    return JarvisApp(
        settings=settings,
        audio_input=audio_input,
        audio_output=audio_output,
        query_recorder=query_recorder,
        wakeword_detector=wakeword_detector,
        debouncer=debouncer,
        stt=stt,
        llm=llm,
        personality=personality,
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
