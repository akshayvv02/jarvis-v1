from __future__ import annotations

import pytest

from jarvis.personality import JarvisPersonality, PersonalityConfig


@pytest.mark.parametrize("level", [0, 1, 2, 3])
def test_personality_prompt_contains_required_behavior(level: int) -> None:
    personality = JarvisPersonality(
        PersonalityConfig(name="indian_casual", humor_level=level)
    )

    prompt = personality.system_prompt()

    assert personality.name == "indian_casual"
    assert personality.version == "jarvis-indian-v1"
    assert personality.humor_level == level
    assert "English, Hindi, Hinglish" in prompt
    assert "spoken aloud" in prompt
    assert "SERIOUS CONTEXT" in prompt
    assert "no tool calling" in prompt
    assert f"Current humor level: {level}" in prompt


def test_personality_rejects_unsupported_profile() -> None:
    with pytest.raises(ValueError, match="JARVIS_PERSONALITY"):
        JarvisPersonality(PersonalityConfig(name="minimal", humor_level=2))


def test_personality_rejects_unsupported_humor_level() -> None:
    with pytest.raises(ValueError, match="JARVIS_HUMOR_LEVEL"):
        JarvisPersonality(PersonalityConfig(name="indian_casual", humor_level=9))
