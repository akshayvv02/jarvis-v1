from __future__ import annotations

from jarvis.wakeword import WakeWordDebouncer, WakeWordDetection


def test_first_detection_is_allowed() -> None:
    debouncer = WakeWordDebouncer(cooldown_ms=1500)
    detection = WakeWordDetection(name="hey_jarvis", score=0.8)

    assert debouncer.allow(detection, now=10.0) == detection


def test_detection_during_cooldown_is_suppressed() -> None:
    debouncer = WakeWordDebouncer(cooldown_ms=1500)
    detection = WakeWordDetection(name="hey_jarvis", score=0.8)

    assert debouncer.allow(detection, now=10.0) == detection
    assert debouncer.allow(detection, now=11.0) is None


def test_detection_after_cooldown_is_allowed() -> None:
    debouncer = WakeWordDebouncer(cooldown_ms=1500)
    detection = WakeWordDetection(name="hey_jarvis", score=0.8)

    assert debouncer.allow(detection, now=10.0) == detection
    assert debouncer.allow(detection, now=11.5) == detection
