from __future__ import annotations

import numpy as np

from jarvis.audio.interface import AudioChunk
from jarvis.wakeword.interface import WakeWordDetection, WakeWordDetector


class FakeDetector:
    def start(self) -> None:
        self.started = True

    def process(self, audio: AudioChunk) -> list[WakeWordDetection]:
        assert audio.sample_rate == 16_000
        return [WakeWordDetection(name="hey_jarvis", score=0.9)]

    def stop(self) -> None:
        self.stopped = True


def test_detector_protocol_shape() -> None:
    detector: WakeWordDetector = FakeDetector()
    audio = AudioChunk(samples=np.zeros(1280, dtype=np.int16), sample_rate=16_000, channels=1)

    detector.start()
    detections = detector.process(audio)
    detector.stop()

    assert detections == [WakeWordDetection(name="hey_jarvis", score=0.9)]
