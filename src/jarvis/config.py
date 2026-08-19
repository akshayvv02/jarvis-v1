from __future__ import annotations

from dataclasses import dataclass
import os
from typing import TypeAlias

AudioDevice: TypeAlias = int | str | None


@dataclass(frozen=True)
class Settings:
    log_level: str = "INFO"
    audio_device: AudioDevice = None
    sample_rate: int = 16_000
    channels: int = 1
    chunk_size: int = 1_280
    wakeword_model: str = "hey_jarvis"
    wakeword_threshold: float = 0.5
    wakeword_cooldown_ms: int = 1_500

    @classmethod
    def from_env(cls) -> "Settings":
        settings = cls(
            log_level=_get_str("JARVIS_LOG_LEVEL", cls.log_level).upper(),
            audio_device=_get_audio_device("JARVIS_AUDIO_DEVICE"),
            sample_rate=_get_int("JARVIS_SAMPLE_RATE", cls.sample_rate),
            channels=_get_int("JARVIS_CHANNELS", cls.channels),
            chunk_size=_get_int("JARVIS_CHUNK_SIZE", cls.chunk_size),
            wakeword_model=_get_str("JARVIS_WAKEWORD_MODEL", cls.wakeword_model),
            wakeword_threshold=_get_float(
                "JARVIS_WAKEWORD_THRESHOLD", cls.wakeword_threshold
            ),
            wakeword_cooldown_ms=_get_int(
                "JARVIS_WAKEWORD_COOLDOWN_MS", cls.wakeword_cooldown_ms
            ),
        )
        settings.validate()
        return settings

    def validate(self) -> None:
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if self.log_level not in valid_levels:
            raise ValueError(
                f"JARVIS_LOG_LEVEL must be one of {sorted(valid_levels)}; "
                f"got {self.log_level!r}"
            )
        if self.sample_rate <= 0:
            raise ValueError("JARVIS_SAMPLE_RATE must be greater than 0")
        if self.channels <= 0:
            raise ValueError("JARVIS_CHANNELS must be greater than 0")
        if self.chunk_size <= 0:
            raise ValueError("JARVIS_CHUNK_SIZE must be greater than 0")
        if not 0 < self.wakeword_threshold <= 1:
            raise ValueError("JARVIS_WAKEWORD_THRESHOLD must be > 0 and <= 1")
        if self.wakeword_cooldown_ms < 0:
            raise ValueError("JARVIS_WAKEWORD_COOLDOWN_MS must be >= 0")
        if not self.wakeword_model.strip():
            raise ValueError("JARVIS_WAKEWORD_MODEL must not be empty")


def _get_optional_str(name: str) -> str | None:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return None
    return value


def _get_audio_device(name: str) -> AudioDevice:
    value = _get_optional_str(name)
    if value is None:
        return None
    if value.isdigit():
        return int(value)
    return value


def _get_str(name: str, default: str) -> str:
    return os.getenv(name, default)


def _get_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer; got {value!r}") from exc


def _get_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    try:
        return float(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be a number; got {value!r}") from exc
