from __future__ import annotations

from collections.abc import Callable, Iterator
import logging
import time
from typing import Any

from jarvis.llm.models import LLMChunk, LLMRequest

logger = logging.getLogger(__name__)


class LLMError(RuntimeError):
    pass


class GeminiProvider:
    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        timeout_seconds: float,
        client: Any | None = None,
        clock: Callable[[], float] = time.perf_counter,
    ) -> None:
        if not api_key.strip():
            raise ValueError("GEMINI_API_KEY is not configured")
        if not model.strip():
            raise ValueError("GEMINI_MODEL must not be empty")
        if timeout_seconds <= 0:
            raise ValueError("GEMINI_REQUEST_TIMEOUT_SECONDS must be > 0")

        self._model = model
        self._clock = clock
        self._client = client or _build_client(
            api_key=api_key,
            timeout_seconds=timeout_seconds,
        )

    def stream(self, request: LLMRequest) -> Iterator[LLMChunk]:
        logger.debug("Generating Gemini response: model=%s", self._model)
        started = self._clock()
        first_token_at: float | None = None
        emitted_chars = 0

        try:
            stream = self._client.models.generate_content_stream(
                model=self._model,
                contents=request.user_text,
                config=_build_generate_config(request.system_prompt),
            )
            for response_chunk in stream:
                text = getattr(response_chunk, "text", None)
                if not text:
                    continue
                if first_token_at is None:
                    first_token_at = self._clock()
                    logger.debug(
                        "LLM first token: provider=gemini model=%s ttft_ms=%.1f",
                        self._model,
                        (first_token_at - started) * 1000,
                    )
                emitted_chars += len(text)
                yield LLMChunk(text=text)
        except Exception as exc:
            if emitted_chars:
                logger.warning(
                    "Gemini stream failed after partial response: chars=%s",
                    emitted_chars,
                )
            raise LLMError(_friendly_error_message(exc)) from exc

        total_ms = (self._clock() - started) * 1000
        if emitted_chars == 0:
            raise LLMError("Gemini returned no usable response")

        ttft_ms = None if first_token_at is None else (first_token_at - started) * 1000
        logger.debug(
            "LLM response completed: provider=gemini model=%s ttft_ms=%s total_ms=%.1f chars=%s",
            self._model,
            "n/a" if ttft_ms is None else f"{ttft_ms:.1f}",
            total_ms,
            emitted_chars,
        )


def _build_client(*, api_key: str, timeout_seconds: float) -> Any:
    from google import genai
    from google.genai import types

    return genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(timeout=int(timeout_seconds * 1000)),
    )


def _build_generate_config(system_prompt: str | None) -> Any:
    from google.genai import types

    return types.GenerateContentConfig(
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        system_instruction=system_prompt if system_prompt and system_prompt.strip() else None,
    )


def _friendly_error_message(exc: Exception) -> str:
    status_code = getattr(exc, "code", None) or getattr(exc, "status_code", None)
    message = str(exc)

    if status_code in {401, 403}:
        return "Gemini authentication failed"
    if status_code == 429:
        return "Gemini rate limit exceeded"
    if isinstance(exc, TimeoutError) or "timeout" in message.lower():
        return "Gemini request timed out"
    if status_code:
        return f"Gemini request failed: status={status_code}"
    return f"Gemini request failed: {message}"
