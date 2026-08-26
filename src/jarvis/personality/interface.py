from __future__ import annotations

from typing import Protocol


class PersonalityProvider(Protocol):
    @property
    def name(self) -> str:
        pass

    @property
    def version(self) -> str:
        pass

    @property
    def humor_level(self) -> int:
        pass

    def system_prompt(self) -> str:
        pass
