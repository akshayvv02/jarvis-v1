from __future__ import annotations

from typing import Protocol

from jarvis.audio.recorder import RecordedAudio
from jarvis.stt.models import Transcript


class SpeechToText(Protocol):
    def transcribe(self, audio: RecordedAudio) -> Transcript:
        ...
