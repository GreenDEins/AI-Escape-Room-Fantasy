"""
Version 1 — thin wrapper around the Google Gemini API.

The full chat history is sent on every turn, so the LLM's "memory" is simply
the conversation itself.
"""

import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

DEFAULT_MODEL = "gemini-3.8-flash"


class GameMasterLLM:
    """Sends the conversation to Gemini and returns the Game Master's reply."""

    def __init__(self, system_prompt: str, api_key: str | None = None, model: str | None = None):
        api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not set. Copy .env.example to .env and add your key."
            )
        self.client = genai.Client(api_key=api_key)
        self.model = model or os.getenv("GEMINI_MODEL", DEFAULT_MODEL)
        self.system_prompt = system_prompt

    def reply(self, history: list[dict]) -> str:
        """
        history: list of {"role": "user" | "assistant", "content": str}
        Gemini uses the role name "model" for the assistant.
        """
        contents = [
            types.Content(
                role="user" if msg["role"] == "user" else "model",
                parts=[types.Part(text=msg["content"])],
            )
            for msg in history
        ]
        response = self.client.models.generate_content(
            model=self.model,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=self.system_prompt,
                temperature=0.8,
            ),
        )
        return (response.text or "").strip()
