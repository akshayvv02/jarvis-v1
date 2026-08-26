from __future__ import annotations

from jarvis.speech import SpeechTextProcessor


def test_speech_text_processor_removes_markdown_and_symbols() -> None:
    processor = SpeechTextProcessor()

    assert processor.process("## Answer\n- Weekend khatam 😭") == "Answer Weekend khatam"
