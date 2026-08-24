from __future__ import annotations

import logging

import requests

from jarvis.audio.recorder import RecordedAudio
from jarvis.stt.models import Transcript

logger = logging.getLogger(__name__)


class STTError(RuntimeError):
    pass


class SarvamSTT:
    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        mode: str,
        language_code: str,
        timeout_seconds: float,
        base_url: str = "https://api.sarvam.ai",
    ) -> None:
        if not api_key.strip():
            raise ValueError("SARVAM_API_KEY is not configured")
        self._api_key = api_key
        self._model = model
        self._mode = mode
        self._language_code = language_code
        self._timeout_seconds = timeout_seconds
        self._url = f"{base_url.rstrip('/')}/speech-to-text"

    def transcribe(self, audio: RecordedAudio) -> Transcript:
        logger.info(
            "Transcribing query audio with Sarvam: model=%s mode=%s language_code=%s",
            self._model,
            self._mode,
            self._language_code,
        )
        try:
            with audio.path.open("rb") as file:
                response = requests.post(
                    self._url,
                    headers={"api-subscription-key": self._api_key},
                    data={
                        "model": self._model,
                        "mode": self._mode,
                        "language_code": self._language_code,
                    },
                    files={"file": (audio.path.name, file, "audio/wav")},
                    timeout=self._timeout_seconds,
                )
        except requests.Timeout as exc:
            raise STTError("STT request timed out") from exc
        except requests.RequestException as exc:
            raise STTError(f"STT request failed: {exc}") from exc

        if response.status_code == 401 or response.status_code == 403:
            raise STTError("STT authentication failed")
        if response.status_code == 429:
            raise STTError("STT rate limit exceeded")
        if response.status_code == 400 or response.status_code == 422:
            raise STTError(f"STT rejected audio: {response.text}")
        if response.status_code >= 400:
            raise STTError(
                f"STT request failed: status={response.status_code} body={response.text}"
            )

        try:
            payload = response.json()
        except ValueError as exc:
            raise STTError("STT response was not valid JSON") from exc

        transcript = payload.get("transcript")
        if not isinstance(transcript, str):
            raise STTError("STT response did not contain a transcript")

        result = Transcript(
            text=transcript,
            language_code=payload.get("language_code"),
            request_id=payload.get("request_id"),
        )
        logger.info("Transcription completed")
        return result
