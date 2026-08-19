from __future__ import annotations

from dataclasses import dataclass
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

    def stop(self) -> None:
        ...
