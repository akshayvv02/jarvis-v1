from __future__ import annotations

import logging

from jarvis.audio.interface import AudioChunk
from jarvis.wakeword.interface import WakeWordDetection

logger = logging.getLogger(__name__)


class OpenWakeWordDetector:
    def __init__(self, *, model_name: str, threshold: float) -> None:
        self._model_name = model_name
        self._threshold = threshold
        self._model = None

    def start(self) -> None:
        try:
            from openwakeword.model import Model

            self._model = Model(
                wakeword_models=[self._model_name],
                inference_framework="onnx",
            )
        except Exception:
            logger.exception("Failed to initialize wake-word detector")
            self._model = None
            raise

        logger.info(
            "Wake-word detector initialized: provider=openWakeWord model=%s threshold=%.3f",
            self._model_name,
            self._threshold,
        )

    def process(self, audio: AudioChunk) -> list[WakeWordDetection]:
        if self._model is None:
            raise RuntimeError("Wake-word detector has not been started")

        predictions = self._model.predict(audio.samples)
        detections: list[WakeWordDetection] = []

        for name, score in predictions.items():
            numeric_score = float(score)
            if numeric_score >= self._threshold:
                detections.append(WakeWordDetection(name=name, score=numeric_score))

        return detections

    def stop(self) -> None:
        self._model = None
        logger.info("Wake-word detector stopped")
