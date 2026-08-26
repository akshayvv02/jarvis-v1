from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TTSRequest:
    text: str
    language_code: str
    speaker: str | None = None

    def __post_init__(self) -> None:
        if not self.text.strip():
            raise ValueError("TTSRequest.text must not be empty")
        if not self.language_code.strip():
            raise ValueError("TTSRequest.language_code must not be empty")


@dataclass(frozen=True)
class TTSAudio:
    audio_bytes: bytes
    format: str
    sample_rate: int | None = None
    request_id: str | None = None

    def __post_init__(self) -> None:
        if not self.audio_bytes:
            raise ValueError("TTSAudio.audio_bytes must not be empty")
        if not self.format.strip():
            raise ValueError("TTSAudio.format must not be empty")
