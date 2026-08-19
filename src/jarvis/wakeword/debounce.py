from __future__ import annotations

from jarvis.wakeword.interface import WakeWordDetection


class WakeWordDebouncer:
    def __init__(self, cooldown_ms: int) -> None:
        if cooldown_ms < 0:
            raise ValueError("cooldown_ms must be >= 0")
        self._cooldown_seconds = cooldown_ms / 1000
        self._last_detection_at: float | None = None

    def allow(self, detection: WakeWordDetection, now: float) -> WakeWordDetection | None:
        if self._last_detection_at is None:
            self._last_detection_at = now
            return detection

        if now - self._last_detection_at >= self._cooldown_seconds:
            self._last_detection_at = now
            return detection

        return None
