from __future__ import annotations

from typing import Protocol

from jarvis.tts.models import TTSAudio, TTSRequest


class TextToSpeech(Protocol):
    def synthesize(self, request: TTSRequest) -> TTSAudio:
        pass
