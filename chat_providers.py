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
        self._has_key = bool(api_key and OpenAI and api_key.strip())
        if self._has_key:
            try:
                # Initialize OpenAI client with API key
                clean_api_key = api_key.strip()
                self.client = OpenAI(api_key=clean_api_key)
            except Exception as e:
                print(f"Error initializing OpenAI client: {e}")
                import traceback
                traceback.print_exc()
                self._has_key = False
                self.client = None
        else:
            self.client = None

    def chat(self, messages: List[Dict[str, str]], model: str | None = None) -> str:
        if self._has_key and self.client:
            use_model = model or os.environ.get('OPENAI_MODEL', 'gpt-4o-mini')
            completion = self.client.chat.completions.create(
                model=use_model,
                messages=messages,
                temperature=0.7,
            )
            return completion.choices[0].message.content or ''
        # Explicit guidance if provider is unavailable to avoid confusing "local mode" output
        return (
            "Provider unavailable: missing OPENAI_API_KEY. Add it to your environment or .env, then "
            "refresh and try again."
        )


def get_default_provider() -> ChatProvider:
    return OpenAIProvider()

