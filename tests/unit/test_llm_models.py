from __future__ import annotations

import pytest

from jarvis.llm.models import LLMRequest


def test_llm_request_rejects_empty_user_text() -> None:
    with pytest.raises(ValueError, match="user_text"):
        LLMRequest(user_text="  ")
