from __future__ import annotations

import re
import unicodedata


class SpeechTextProcessor:
    def process(self, text: str) -> str:
        lines = [_clean_line(line) for line in text.splitlines()]
        cleaned = " ".join(line for line in lines if line)
        cleaned = "".join(
            char for char in cleaned if unicodedata.category(char) != "So"
        )
        cleaned = re.sub(r"[*_`>#]+", "", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned)
        return cleaned.strip()


def _clean_line(line: str) -> str:
    line = line.strip()
    line = re.sub(r"^#{1,6}\s*", "", line)
    line = re.sub(r"^[-*+]\s+", "", line)
    line = re.sub(r"^\d+[.)]\s+", "", line)
    return line
