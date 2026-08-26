from __future__ import annotations

from collections.abc import Iterator
from typing import Protocol

from jarvis.llm.models import LLMChunk, LLMRequest


class LLMProvider(Protocol):
    def stream(self, request: LLMRequest) -> Iterator[LLMChunk]:
        pass
