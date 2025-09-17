import os
from typing import List, Dict
from openai import OpenAI


class ChatProvider:
    def chat(self, messages: List[Dict[str, str]], model: str | None = None) -> str:
        raise NotImplementedError


class OpenAIProvider(ChatProvider):
    def __init__(self) -> None:
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            raise RuntimeError('OPENAI_API_KEY is not set')
        self.client = OpenAI(api_key=api_key)

    def chat(self, messages: List[Dict[str, str]], model: str | None = None) -> str:
        use_model = model or os.environ.get('OPENAI_MODEL', 'gpt-4o-mini')
        completion = self.client.chat.completions.create(
            model=use_model,
            messages=messages,
            temperature=0.7,
        )
        return completion.choices[0].message.content or ''


def get_default_provider() -> ChatProvider:
    return OpenAIProvider()

