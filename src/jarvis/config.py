from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
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
    wakeword_resume_delay_ms: int = 1_500
    wakeword_reset_duration_ms: int = 1_500
    ack_audio_path: Path = Path("assets/audio/acknowledgement.wav")
    audio_output_device: AudioDevice = None
    audio_flush_duration_ms: int = 300
    query_max_duration_seconds: float = 30.0
    query_no_speech_timeout_seconds: float = 5.0
    silence_duration_ms: int = 1_000
    speech_start_threshold: float = 500.0
    query_temp_dir: Path = Path("/tmp/jarvis")
    cleanup_query_audio: bool = True
    sarvam_api_key: str | None = None
    sarvam_stt_model: str = "saaras:v3"
    sarvam_stt_mode: str = "transcribe"
    sarvam_stt_language_code: str = "unknown"
    sarvam_stt_timeout_seconds: float = 30.0
    sarvam_tts_model: str = "bulbul:v3"
    sarvam_tts_speaker: str = "priya"
    sarvam_tts_language: str = "en-IN"
    sarvam_tts_pace: float = 1.0
    sarvam_tts_output_format: str = "wav"
    sarvam_tts_timeout_seconds: float = 30.0
    tts_temp_dir: Path = Path("/tmp/jarvis")
    cleanup_tts_audio: bool = True
    llm_provider: str = "gemini"
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-3.5-flash-lite"
    gemini_request_timeout_seconds: float = 30.0
    personality: str = "indian_casual"
    humor_level: int = 2
    prompt_debug: bool = False

    @classmethod
    def from_env(cls, env_file: Path | None = Path(".env")) -> "Settings":
        if env_file is not None:
            load_env_file(env_file)
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
            wakeword_resume_delay_ms=_get_int(
                "JARVIS_WAKEWORD_RESUME_DELAY_MS", cls.wakeword_resume_delay_ms
            ),
            wakeword_reset_duration_ms=_get_int(
                "JARVIS_WAKEWORD_RESET_DURATION_MS", cls.wakeword_reset_duration_ms
            ),
            ack_audio_path=Path(_get_str("JARVIS_ACK_AUDIO_PATH", str(cls.ack_audio_path))),
            audio_output_device=_get_audio_device("JARVIS_AUDIO_OUTPUT_DEVICE"),
            audio_flush_duration_ms=_get_int(
                "JARVIS_AUDIO_FLUSH_DURATION_MS", cls.audio_flush_duration_ms
            ),
            query_max_duration_seconds=_get_float(
                "JARVIS_QUERY_MAX_DURATION_SECONDS",
                cls.query_max_duration_seconds,
            ),
            query_no_speech_timeout_seconds=_get_float(
                "JARVIS_QUERY_NO_SPEECH_TIMEOUT_SECONDS",
                cls.query_no_speech_timeout_seconds,
            ),
            silence_duration_ms=_get_int(
                "JARVIS_SILENCE_DURATION_MS", cls.silence_duration_ms
            ),
            speech_start_threshold=_get_float(
                "JARVIS_SPEECH_START_THRESHOLD", cls.speech_start_threshold
            ),
            query_temp_dir=Path(
                _get_str("JARVIS_QUERY_TEMP_DIR", str(cls.query_temp_dir))
            ),
            cleanup_query_audio=_get_bool(
                "JARVIS_CLEANUP_QUERY_AUDIO", cls.cleanup_query_audio
            ),
            sarvam_api_key=_get_optional_str("SARVAM_API_KEY"),
            sarvam_stt_model=_get_str("SARVAM_STT_MODEL", cls.sarvam_stt_model),
            sarvam_stt_mode=_get_str("SARVAM_STT_MODE", cls.sarvam_stt_mode),
            sarvam_stt_language_code=_get_str(
                "SARVAM_STT_LANGUAGE_CODE",
                cls.sarvam_stt_language_code,
            ),
            sarvam_stt_timeout_seconds=_get_float(
                "SARVAM_STT_TIMEOUT_SECONDS",
                cls.sarvam_stt_timeout_seconds,
            ),
            sarvam_tts_model=_get_str("SARVAM_TTS_MODEL", cls.sarvam_tts_model),
            sarvam_tts_speaker=_get_str(
                "SARVAM_TTS_SPEAKER",
                cls.sarvam_tts_speaker,
            ),
            sarvam_tts_language=_get_str(
                "SARVAM_TTS_LANGUAGE",
                cls.sarvam_tts_language,
            ),
            sarvam_tts_pace=_get_float("SARVAM_TTS_PACE", cls.sarvam_tts_pace),
            sarvam_tts_output_format=_get_str(
                "SARVAM_TTS_OUTPUT_FORMAT",
                cls.sarvam_tts_output_format,
            ),
            sarvam_tts_timeout_seconds=_get_float(
                "SARVAM_TTS_TIMEOUT_SECONDS",
                cls.sarvam_tts_timeout_seconds,
            ),
            tts_temp_dir=Path(_get_str("JARVIS_TTS_TEMP_DIR", str(cls.tts_temp_dir))),
            cleanup_tts_audio=_get_bool(
                "JARVIS_CLEANUP_TTS_AUDIO",
                cls.cleanup_tts_audio,
            ),
            llm_provider=_get_str("JARVIS_LLM_PROVIDER", cls.llm_provider)
            .strip()
            .lower(),
            gemini_api_key=_get_optional_str("GEMINI_API_KEY"),
            gemini_model=_get_str("GEMINI_MODEL", cls.gemini_model),
            gemini_request_timeout_seconds=_get_float(
                "GEMINI_REQUEST_TIMEOUT_SECONDS",
                cls.gemini_request_timeout_seconds,
            ),
            personality=_get_str("JARVIS_PERSONALITY", cls.personality)
            .strip()
            .lower(),
            humor_level=_get_int("JARVIS_HUMOR_LEVEL", cls.humor_level),
            prompt_debug=_get_bool("JARVIS_PROMPT_DEBUG", cls.prompt_debug),
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
        if self.wakeword_resume_delay_ms < 0:
            raise ValueError("JARVIS_WAKEWORD_RESUME_DELAY_MS must be >= 0")
        if self.wakeword_reset_duration_ms < 0:
            raise ValueError("JARVIS_WAKEWORD_RESET_DURATION_MS must be >= 0")
        if not self.wakeword_model.strip():
            raise ValueError("JARVIS_WAKEWORD_MODEL must not be empty")
        if not self.ack_audio_path:
            raise ValueError("JARVIS_ACK_AUDIO_PATH must not be empty")
        if self.audio_flush_duration_ms < 0:
            raise ValueError("JARVIS_AUDIO_FLUSH_DURATION_MS must be >= 0")
        if not 0 < self.query_max_duration_seconds <= 30:
            raise ValueError("JARVIS_QUERY_MAX_DURATION_SECONDS must be > 0 and <= 30")
        if self.query_no_speech_timeout_seconds <= 0:
            raise ValueError("JARVIS_QUERY_NO_SPEECH_TIMEOUT_SECONDS must be > 0")
        if self.silence_duration_ms <= 0:
            raise ValueError("JARVIS_SILENCE_DURATION_MS must be > 0")
        if self.speech_start_threshold <= 0:
            raise ValueError("JARVIS_SPEECH_START_THRESHOLD must be > 0")
        if not self.sarvam_stt_model.strip():
            raise ValueError("SARVAM_STT_MODEL must not be empty")
        if not self.sarvam_stt_mode.strip():
            raise ValueError("SARVAM_STT_MODE must not be empty")
        if not self.sarvam_stt_language_code.strip():
            raise ValueError("SARVAM_STT_LANGUAGE_CODE must not be empty")
        if self.sarvam_stt_timeout_seconds <= 0:
            raise ValueError("SARVAM_STT_TIMEOUT_SECONDS must be > 0")
        if not self.sarvam_tts_model.strip():
            raise ValueError("SARVAM_TTS_MODEL must not be empty")
        if not self.sarvam_tts_speaker.strip():
            raise ValueError("SARVAM_TTS_SPEAKER must not be empty")
        if self.sarvam_tts_speaker != self.sarvam_tts_speaker.lower():
            raise ValueError("SARVAM_TTS_SPEAKER must be lowercase")
        if self.sarvam_tts_language not in {"en-IN", "hi-IN"}:
            raise ValueError("SARVAM_TTS_LANGUAGE must be 'en-IN' or 'hi-IN'")
        if not 0.5 <= self.sarvam_tts_pace <= 2.0:
            raise ValueError("SARVAM_TTS_PACE must be between 0.5 and 2.0")
        if self.sarvam_tts_output_format != "wav":
            raise ValueError("SARVAM_TTS_OUTPUT_FORMAT must be 'wav'")
        if self.sarvam_tts_timeout_seconds <= 0:
            raise ValueError("SARVAM_TTS_TIMEOUT_SECONDS must be > 0")
        if self.llm_provider != "gemini":
            raise ValueError("JARVIS_LLM_PROVIDER must be 'gemini'")
        if not self.gemini_model.strip():
            raise ValueError("GEMINI_MODEL must not be empty")
        if self.gemini_request_timeout_seconds <= 0:
            raise ValueError("GEMINI_REQUEST_TIMEOUT_SECONDS must be > 0")
        if self.personality != "indian_casual":
            raise ValueError("JARVIS_PERSONALITY must be 'indian_casual'")
        if self.humor_level not in {0, 1, 2, 3}:
            raise ValueError("JARVIS_HUMOR_LEVEL must be one of 0, 1, 2, or 3")


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


def load_env_file(path: Path) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        name, value = line.split("=", 1)
        name = name.strip()
        value = value.strip().strip('"').strip("'")
        if name and name not in os.environ:
            os.environ[name] = value


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


def _get_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"{name} must be a boolean; got {value!r}")
