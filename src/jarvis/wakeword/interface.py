from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from jarvis.audio.interface import AudioChunk


@dataclass(frozen=True)
class WakeWordDetection:
    name: str
    score: float


class WakeWordDetector(Protocol):
    def start(self) -> None:
        ...

    def process(self, audio: AudioChunk) -> list[WakeWordDetection]:
        ...

    def stop(self) -> None:
        ...
