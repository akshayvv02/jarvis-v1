from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import numpy as np
import numpy.typing as npt


@dataclass(frozen=True)
class AudioChunk:
    samples: npt.NDArray[np.int16]
    sample_rate: int
    channels: int


class AudioInput(Protocol):
    def start(self) -> None:
        ...

    def read(self) -> AudioChunk:
        ...

    def flush(self, duration_ms: int) -> None:
        ...

    def stop(self) -> None:
        ...


class AudioOutput(Protocol):
    def play(self, audio_file: Path) -> None:
        ...
