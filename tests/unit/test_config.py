from __future__ import annotations

import pytest

from jarvis.config import Settings


def test_defaults_load(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in [
        "JARVIS_LOG_LEVEL",
        "JARVIS_AUDIO_DEVICE",
        "JARVIS_SAMPLE_RATE",
        "JARVIS_CHANNELS",
        "JARVIS_CHUNK_SIZE",
        "JARVIS_WAKEWORD_MODEL",
        "JARVIS_WAKEWORD_THRESHOLD",
        "JARVIS_WAKEWORD_COOLDOWN_MS",
    ]:
        monkeypatch.delenv(name, raising=False)

    settings = Settings.from_env()

    assert settings.log_level == "INFO"
    assert settings.audio_device is None
    assert settings.sample_rate == 16_000
    assert settings.channels == 1
    assert settings.chunk_size == 1_280
    assert settings.wakeword_model == "hey_jarvis"
    assert settings.wakeword_threshold == 0.5
    assert settings.wakeword_cooldown_ms == 1_500


def test_environment_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JARVIS_LOG_LEVEL", "debug")
    monkeypatch.setenv("JARVIS_AUDIO_DEVICE", "hw:1,0")
    monkeypatch.setenv("JARVIS_SAMPLE_RATE", "8000")
    monkeypatch.setenv("JARVIS_CHANNELS", "2")
    monkeypatch.setenv("JARVIS_CHUNK_SIZE", "640")
    monkeypatch.setenv("JARVIS_WAKEWORD_MODEL", "custom_model")
    monkeypatch.setenv("JARVIS_WAKEWORD_THRESHOLD", "0.75")
    monkeypatch.setenv("JARVIS_WAKEWORD_COOLDOWN_MS", "900")

    settings = Settings.from_env()

    assert settings.log_level == "DEBUG"
    assert settings.audio_device == "hw:1,0"
    assert settings.sample_rate == 8_000
    assert settings.channels == 2
    assert settings.chunk_size == 640
    assert settings.wakeword_model == "custom_model"
    assert settings.wakeword_threshold == 0.75
    assert settings.wakeword_cooldown_ms == 900


def test_invalid_threshold_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JARVIS_WAKEWORD_THRESHOLD", "1.5")

    with pytest.raises(ValueError, match="JARVIS_WAKEWORD_THRESHOLD"):
        Settings.from_env()


def test_invalid_integer_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JARVIS_SAMPLE_RATE", "fast")

    with pytest.raises(ValueError, match="JARVIS_SAMPLE_RATE"):
        Settings.from_env()
