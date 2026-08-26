from __future__ import annotations

import os

import pytest

from jarvis.llm import GeminiProvider
from jarvis.llm.models import LLMRequest
from jarvis.personality import JarvisPersonality, PersonalityConfig


@pytest.mark.integration
def test_gemini_streaming_integration() -> None:
    if os.getenv("GEMINI_INTEGRATION_TESTS") != "true":
        pytest.skip("Set GEMINI_INTEGRATION_TESTS=true to call Gemini")

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        pytest.skip("GEMINI_API_KEY is required")

    provider = GeminiProvider(
        api_key=api_key,
        model=os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite"),
        timeout_seconds=30,
    )
    text = "".join(
        chunk.text for chunk in provider.stream(LLMRequest(user_text="Reply with pong."))
    )

    assert text.strip()


@pytest.mark.integration
def test_gemini_personality_integration() -> None:
    if os.getenv("GEMINI_INTEGRATION_TESTS") != "true":
        pytest.skip("Set GEMINI_INTEGRATION_TESTS=true to call Gemini")

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        pytest.skip("GEMINI_API_KEY is required")

    provider = GeminiProvider(
        api_key=api_key,
        model=os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite"),
        timeout_seconds=30,
    )
    personality = JarvisPersonality(PersonalityConfig())
    text = "".join(
        chunk.text
        for chunk in provider.stream(
            LLMRequest(
                user_text="Bhai reply sirf ek short line mein kar aur bata 2+2 kya hai.",
                system_prompt=personality.system_prompt(),
            )
        )
    )

    assert text.strip()
    assert len(text.split()) <= 30
