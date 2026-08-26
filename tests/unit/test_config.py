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
        "JARVIS_WAKEWORD_RESUME_DELAY_MS",
        "JARVIS_WAKEWORD_RESET_DURATION_MS",
        "JARVIS_LLM_PROVIDER",
        "GEMINI_API_KEY",
        "GEMINI_MODEL",
        "GEMINI_REQUEST_TIMEOUT_SECONDS",
        "JARVIS_PERSONALITY",
        "JARVIS_HUMOR_LEVEL",
        "JARVIS_PROMPT_DEBUG",
        "SARVAM_TTS_MODEL",
        "SARVAM_TTS_SPEAKER",
        "SARVAM_TTS_LANGUAGE",
        "SARVAM_TTS_PACE",
        "SARVAM_TTS_OUTPUT_FORMAT",
        "SARVAM_TTS_TIMEOUT_SECONDS",
    ]:
        monkeypatch.delenv(name, raising=False)

    settings = Settings.from_env(env_file=None)

    assert settings.log_level == "INFO"
    assert settings.audio_device is None
    assert settings.sample_rate == 16_000
    assert settings.channels == 1
    assert settings.chunk_size == 1_280
    assert settings.wakeword_model == "hey_jarvis"
    assert settings.wakeword_threshold == 0.5
    assert settings.wakeword_cooldown_ms == 1_500
    assert settings.wakeword_resume_delay_ms == 1_500
    assert settings.wakeword_reset_duration_ms == 1_500
    assert settings.llm_provider == "gemini"
    assert settings.gemini_api_key is None
    assert settings.gemini_model == "gemini-3.5-flash-lite"
    assert settings.gemini_request_timeout_seconds == 30.0
    assert settings.personality == "indian_casual"
    assert settings.humor_level == 2
    assert settings.prompt_debug is False
    assert settings.sarvam_tts_model == "bulbul:v3"
    assert settings.sarvam_tts_speaker == "priya"
    assert settings.sarvam_tts_language == "en-IN"
    assert settings.sarvam_tts_pace == 1.0
    assert settings.sarvam_tts_output_format == "wav"
    assert settings.sarvam_tts_timeout_seconds == 30.0


def test_environment_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JARVIS_LOG_LEVEL", "debug")
    monkeypatch.setenv("JARVIS_AUDIO_DEVICE", "hw:1,0")
    monkeypatch.setenv("JARVIS_SAMPLE_RATE", "8000")
    monkeypatch.setenv("JARVIS_CHANNELS", "2")
    monkeypatch.setenv("JARVIS_CHUNK_SIZE", "640")
    monkeypatch.setenv("JARVIS_WAKEWORD_MODEL", "custom_model")
    monkeypatch.setenv("JARVIS_WAKEWORD_THRESHOLD", "0.75")
    monkeypatch.setenv("JARVIS_WAKEWORD_COOLDOWN_MS", "900")
    monkeypatch.setenv("JARVIS_WAKEWORD_RESUME_DELAY_MS", "700")
    monkeypatch.setenv("JARVIS_WAKEWORD_RESET_DURATION_MS", "600")
    monkeypatch.setenv("JARVIS_LLM_PROVIDER", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-key")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-test-model")
    monkeypatch.setenv("GEMINI_REQUEST_TIMEOUT_SECONDS", "12")
    monkeypatch.setenv("JARVIS_PERSONALITY", "INDIAN_CASUAL")
    monkeypatch.setenv("JARVIS_HUMOR_LEVEL", "3")
    monkeypatch.setenv("JARVIS_PROMPT_DEBUG", "true")
    monkeypatch.setenv("SARVAM_TTS_MODEL", "bulbul:v3")
    monkeypatch.setenv("SARVAM_TTS_SPEAKER", "ishita")
    monkeypatch.setenv("SARVAM_TTS_LANGUAGE", "hi-IN")
    monkeypatch.setenv("SARVAM_TTS_PACE", "1.1")
    monkeypatch.setenv("SARVAM_TTS_OUTPUT_FORMAT", "wav")
    monkeypatch.setenv("SARVAM_TTS_TIMEOUT_SECONDS", "15")

    settings = Settings.from_env(env_file=None)

    assert settings.log_level == "DEBUG"
    assert settings.audio_device == "hw:1,0"
    assert settings.sample_rate == 8_000
    assert settings.channels == 2
    assert settings.chunk_size == 640
    assert settings.wakeword_model == "custom_model"
    assert settings.wakeword_threshold == 0.75
    assert settings.wakeword_cooldown_ms == 900
    assert settings.wakeword_resume_delay_ms == 700
    assert settings.wakeword_reset_duration_ms == 600
    assert settings.llm_provider == "gemini"
    assert settings.gemini_api_key == "test-gemini-key"
    assert settings.gemini_model == "gemini-test-model"
    assert settings.gemini_request_timeout_seconds == 12.0
    assert settings.personality == "indian_casual"
    assert settings.humor_level == 3
    assert settings.prompt_debug is True
    assert settings.sarvam_tts_speaker == "ishita"
    assert settings.sarvam_tts_language == "hi-IN"
    assert settings.sarvam_tts_pace == 1.1
    assert settings.sarvam_tts_timeout_seconds == 15.0


def test_invalid_threshold_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JARVIS_WAKEWORD_THRESHOLD", "1.5")

    with pytest.raises(ValueError, match="JARVIS_WAKEWORD_THRESHOLD"):
        Settings.from_env(env_file=None)


def test_invalid_integer_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JARVIS_SAMPLE_RATE", "fast")

    with pytest.raises(ValueError, match="JARVIS_SAMPLE_RATE"):
        Settings.from_env(env_file=None)


def test_numeric_audio_device_is_converted_to_int(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("JARVIS_AUDIO_DEVICE", "1")

    settings = Settings.from_env(env_file=None)

    assert settings.audio_device == 1


def test_invalid_llm_provider_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JARVIS_LLM_PROVIDER", "other")

    with pytest.raises(ValueError, match="JARVIS_LLM_PROVIDER"):
        Settings.from_env(env_file=None)


def test_invalid_humor_level_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JARVIS_HUMOR_LEVEL", "4")

    with pytest.raises(ValueError, match="JARVIS_HUMOR_LEVEL"):
        Settings.from_env(env_file=None)


def test_invalid_tts_pace_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SARVAM_TTS_PACE", "2.5")

    with pytest.raises(ValueError, match="SARVAM_TTS_PACE"):
        Settings.from_env(env_file=None)
