import os
from typing import List, Dict
try:
    from openai import OpenAI
except Exception:  # pragma: no cover
    OpenAI = None  # type: ignore


class ChatProvider:
    def chat(self, messages: List[Dict[str, str]], model: str | None = None) -> str:
        raise NotImplementedError


class OpenAIProvider(ChatProvider):
    def __init__(self) -> None:
        api_key = os.environ.get('OPENAI_API_KEY')
        self._has_key = bool(api_key and OpenAI)
        self.client = OpenAI(api_key=api_key) if self._has_key else None

    def chat(self, messages: List[Dict[str, str]], model: str | None = None) -> str:
        if self._has_key and self.client:
            use_model = model or os.environ.get('OPENAI_MODEL', 'gpt-4o-mini')
            completion = self.client.chat.completions.create(
                model=use_model,
                messages=messages,
                temperature=0.7,
            )
            return completion.choices[0].message.content or ''
        # Fallback lightweight guidance when no API key is configured
        # Heuristic: echo last user message, add Socratic prompts and next steps
        last_user = next((m['content'] for m in reversed(messages) if m.get('role') == 'user'), '')
        style_hint = next((m['content'] for m in messages if m.get('role') == 'system'), '')
        prompt = last_user.strip() or 'your topic'
        parts = [
            "(Local mode) Let's explore this together without an external model.",
            f"You asked about: {prompt}.",
        ]
        if 'Socratic' in style_hint:
            parts.append("First, what do you already know about this? What seems unclear?")
        parts.extend([
            "Proposed steps:",
            "1) Define core terms and assumptions",
            "2) Work a small example",
            "3) Generalize and check edge cases",
            "4) Reflect: where does this connect in a broader concept map?",
            "Reply with your initial thoughts or ask for a step-by-step outline.",
        ])
        return "\n".join(parts)


def get_default_provider() -> ChatProvider:
    return OpenAIProvider()

