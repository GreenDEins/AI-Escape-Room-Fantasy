"""
Checks which Gemini models answer with your API key, and how fast.

    python scripts/check_models.py
    python scripts/check_models.py gemini-3.6-flash gemini-3.8-flash

Pick a fast model that says OK and put it into .env as GEMINI_MODEL=...
Model availability changes over time; this script was used to choose the default.
"""

import os
import sys
import time

from dotenv import load_dotenv
from google import genai
from google.genai import types

DEFAULT_MODELS = ["gemini-3.5-flash-lite", "gemini-3.6-flash", "gemini-3.1-flash-lite", "gemini-3.8-flash"]


def main() -> None:
    load_dotenv()
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        sys.exit("GEMINI_API_KEY is not set. Copy .env.example to .env and add your key.")
    client = genai.Client(api_key=key, http_options=types.HttpOptions(
        timeout=60_000, retry_options=types.HttpRetryOptions(attempts=1)))
    for model in sys.argv[1:] or DEFAULT_MODELS:
        start = time.time()
        try:
            reply = client.models.generate_content(model=model, contents="Say hi in five words")
            print(f"OK   {model:24} {time.time() - start:5.1f}s  {(reply.text or '').strip()[:60]}")
        except Exception as err:  # unknown model, quota, timeout...
            print(f"FAIL {model:24} {time.time() - start:5.1f}s  {str(err)[:90]}")


if __name__ == "__main__":
    main()
