from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PersonalityConfig:
    name: str = "indian_casual"
    humor_level: int = 2
    prompt_debug: bool = False

    def validate(self) -> None:
        if self.name != "indian_casual":
            raise ValueError("JARVIS_PERSONALITY must be 'indian_casual'")
        if self.humor_level not in {0, 1, 2, 3}:
            raise ValueError("JARVIS_HUMOR_LEVEL must be one of 0, 1, 2, or 3")
