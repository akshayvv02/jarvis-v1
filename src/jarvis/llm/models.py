from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LLMRequest:
    user_text: str
    system_prompt: str | None = None

    def __post_init__(self) -> None:
        if not self.user_text.strip():
            raise ValueError("LLMRequest.user_text must not be empty")


@dataclass(frozen=True)
class LLMChunk:
    text: str


@dataclass(frozen=True)
class LLMResponse:
    text: str
    model: str
    finish_reason: str | None = None
    request_id: str | None = None
    ttft_ms: float | None = None
    total_ms: float | None = None
