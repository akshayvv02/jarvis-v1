from __future__ import annotations

import base64
import logging
from typing import Any

import requests

from jarvis.tts.models import TTSAudio, TTSRequest

logger = logging.getLogger(__name__)


class TTSError(RuntimeError):
    pass


class SarvamTTS:
    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        speaker: str,
        pace: float,
        output_format: str,
        timeout_seconds: float,
        base_url: str = "https://api.sarvam.ai",
        session: Any = requests,
    ) -> None:
        if not api_key.strip():
            raise ValueError("SARVAM_API_KEY is not configured")
        if not model.strip():
            raise ValueError("SARVAM_TTS_MODEL must not be empty")
        if not speaker.strip():
            raise ValueError("SARVAM_TTS_SPEAKER must not be empty")
        if not 0.5 <= pace <= 2.0:
            raise ValueError("SARVAM_TTS_PACE must be between 0.5 and 2.0")
        if output_format != "wav":
            raise ValueError("SARVAM_TTS_OUTPUT_FORMAT must be 'wav'")
        if timeout_seconds <= 0:
            raise ValueError("SARVAM_TTS_TIMEOUT_SECONDS must be > 0")

        self._api_key = api_key
        self._model = model
        self._speaker = speaker
        self._pace = pace
        self._output_format = output_format
        self._timeout_seconds = timeout_seconds
        self._url = f"{base_url.rstrip('/')}/text-to-speech"
        self._session = session

    def synthesize(self, request: TTSRequest) -> TTSAudio:
        speaker = request.speaker or self._speaker
        logger.info(
            "Generating speech with Sarvam: model=%s speaker=%s language_code=%s pace=%.2f",
            self._model,
            speaker,
            request.language_code,
            self._pace,
        )
        try:
            response = self._session.post(
                self._url,
                headers={"api-subscription-key": self._api_key},
                json={
                    "text": request.text,
                    "language_code": request.language_code,
                    "model": self._model,
                    "speaker": speaker,
                    "pace": self._pace,
                    "output_audio_codec": self._output_format,
                },
                timeout=self._timeout_seconds,
            )
        except requests.Timeout as exc:
            raise TTSError("TTS request timed out") from exc
        except requests.RequestException as exc:
            raise TTSError(f"TTS request failed: {exc}") from exc

        if response.status_code == 401 or response.status_code == 403:
            raise TTSError("TTS authentication failed")
        if response.status_code == 429:
            raise TTSError("TTS rate limit exceeded")
        if response.status_code == 400 or response.status_code == 422:
            raise TTSError(f"TTS request rejected: {response.text}")
        if response.status_code >= 400:
            raise TTSError(
                f"TTS request failed: status={response.status_code} body={response.text}"
            )

        try:
            payload = response.json()
        except ValueError as exc:
            raise TTSError("TTS response was not valid JSON") from exc

        audios = payload.get("audios")
        if not isinstance(audios, list) or not audios:
            raise TTSError("TTS response did not contain audio")

        try:
            audio_bytes = base64.b64decode("".join(audios), validate=True)
        except (ValueError, TypeError) as exc:
            raise TTSError("TTS response audio was not valid base64") from exc

        if not audio_bytes:
            raise TTSError("TTS response audio was empty")

        logger.info("TTS synthesis completed")
        return TTSAudio(
            audio_bytes=audio_bytes,
            format=self._output_format,
            sample_rate=None,
            request_id=payload.get("request_id"),
        )
