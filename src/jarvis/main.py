from __future__ import annotations

import logging
import signal
import time

from jarvis.audio import AudioInput
from jarvis.audio.microphone import SoundDeviceMicrophone
from jarvis.config import Settings
from jarvis.logging_config import configure_logging
from jarvis.wakeword import OpenWakeWordDetector, WakeWordDebouncer, WakeWordDetector

logger = logging.getLogger(__name__)


class JarvisApp:
    def __init__(
        self,
        *,
        settings: Settings,
        audio_input: AudioInput,
        wakeword_detector: WakeWordDetector,
        debouncer: WakeWordDebouncer,
    ) -> None:
        self._settings = settings
        self._audio_input = audio_input
        self._wakeword_detector = wakeword_detector
        self._debouncer = debouncer
        self._running = False

    def request_shutdown(self, signum: int, _frame: object) -> None:
        logger.info("Shutdown requested: signal=%s", signum)
        self._running = False

    def run(self) -> int:
        logger.info("Jarvis starting")
        try:
            self._wakeword_detector.start()
            self._audio_input.start()
            self._running = True

            logger.info('Listening for "Hey Jarvis"...')
            while self._running:
                chunk = self._audio_input.read()
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
        finally:
            self._audio_input.stop()
            self._wakeword_detector.stop()
            logger.info("Jarvis stopped")

        return 0


def build_app(settings: Settings) -> JarvisApp:
    audio_input = SoundDeviceMicrophone(
        device=settings.audio_device,
        sample_rate=settings.sample_rate,
        channels=settings.channels,
        chunk_size=settings.chunk_size,
    )
    wakeword_detector = OpenWakeWordDetector(
        model_name=settings.wakeword_model,
        threshold=settings.wakeword_threshold,
    )
    debouncer = WakeWordDebouncer(cooldown_ms=settings.wakeword_cooldown_ms)
    return JarvisApp(
        settings=settings,
        audio_input=audio_input,
        wakeword_detector=wakeword_detector,
        debouncer=debouncer,
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
