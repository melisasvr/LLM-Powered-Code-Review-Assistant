"""
model_client.py
---------------
Handles Groq API client initialization and model configuration.
Groq gives us fast, free inference — no local GPU needed.
"""

import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Available models on Groq (as of 2025) — ordered by code review quality
# ---------------------------------------------------------------------------
MODELS = {
    "llama-3.3-70b-versatile": {
        "label": "Llama 3.3 70B (Best quality)",
        "context_window": 128_000,
        "recommended": True,
    },
    "llama-3.1-8b-instant": {
        "label": "Llama 3.1 8B (Fastest / lightest)",
        "context_window": 128_000,
        "recommended": False,
    },
    "deepseek-r1-distill-llama-70b": {
        "label": "DeepSeek R1 70B (Strong reasoning)",
        "context_window": 128_000,
        "recommended": False,
    },
    "qwen-qwq-32b": {
        "label": "Qwen QwQ 32B (Excellent for code)",
        "context_window": 128_000,
        "recommended": False,
    },
}

DEFAULT_MODEL = "llama-3.3-70b-versatile"


def get_client() -> Groq:
    """
    Initialize and return a Groq client.
    Reads GROQ_API_KEY from environment / .env file.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "GROQ_API_KEY not found. "
            "Set it in your .env file or as an environment variable.\n"
            "Get a free key at: https://console.groq.com/keys"
        )
    return Groq(api_key=api_key)