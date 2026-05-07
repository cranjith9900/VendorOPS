from __future__ import annotations

import json
import os
from typing import Any


class AnthropicJsonFallback:
    """Small optional adapter used only when rule lookup cannot decide."""

    def __init__(self, model: str = "claude-3-5-sonnet-latest") -> None:
        self.model = model

    @property
    def enabled(self) -> bool:
        return bool(os.getenv("ANTHROPIC_API_KEY"))

    def complete_json(self, system_prompt: str, payload: dict[str, Any]) -> dict[str, Any] | None:
        if not self.enabled:
            return None

        try:
            import anthropic
        except ImportError:
            return None

        client = anthropic.Anthropic()
        response = client.messages.create(
            model=self.model,
            max_tokens=500,
            temperature=0,
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": json.dumps(payload, sort_keys=True),
                }
            ],
        )
        text = "".join(
            block.text for block in response.content if getattr(block, "type", None) == "text"
        )
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            return None
        return parsed if isinstance(parsed, dict) else None
