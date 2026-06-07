from groq import Groq
import os
import logging
from typing import AsyncGenerator

MODEL = "llama-3.3-70b-versatile"  # Fast, capable model on Groq
MAX_TOKENS = 4096

logger = logging.getLogger("groq_client")

# Lazy client — initialized on first use to avoid crashing startup
# if GROQ_API_KEY is not yet set in the environment
_client = None


def _read_secret_file_candidates():
    """Return candidate paths to check for a GROQ_API_KEY secret file."""
    return [
        "/etc/secrets/GROQ_API_KEY",
        "/etc/secrets/groq_api_key",
        "./.env",
        "./secrets/GROQ_API_KEY",
        "./secrets/groq_api_key",
    ]


def _read_key_from_env_or_secretfile() -> str | None:
    # 1) env var
    api_key = os.getenv("GROQ_API_KEY")
    if api_key:
        return api_key.strip()

    # 2) files placed by Render's Secret Files feature (or local .env)
    for path in _read_secret_file_candidates():
        try:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                if path.endswith(".env"):
                    # parse simple .env KEY=VALUE lines
                    for line in content.splitlines():
                        line = line.strip()
                        if not line or line.startswith("#") or "=" not in line:
                            continue
                        k, v = line.split("=", 1)
                        if k.strip() == "GROQ_API_KEY":
                            return v.strip().strip('"').strip("'")
                else:
                    # file contains the key directly
                    return content
        except Exception as e:
            logger.exception("Error reading secret file %s: %s", path, e)

    return None


def _get_client() -> Groq:
    global _client
    if _client is None:
        api_key = _read_key_from_env_or_secretfile()
        if not api_key:
            raise RuntimeError(
                "GROQ_API_KEY not set. Set the GROQ_API_KEY environment variable or add a secret file (Render: /etc/secrets/GROQ_API_KEY or add a .env containing GROQ_API_KEY)."
            )
        _client = Groq(api_key=api_key)
    return _client


def stream_response(
    system_prompt: str,
    messages: list[dict],
    max_tokens: int = MAX_TOKENS,
):
    """Stream a response from Groq as server-sent events."""
    groq_messages = [{"role": "system", "content": system_prompt}] + messages

    stream = _get_client().chat.completions.create(
        model=MODEL,
        max_tokens=max_tokens,
        messages=groq_messages,
        stream=True,
    )

    def _generator():
        for chunk in stream:
            # guard against missing attributes on error responses
            try:
                text = chunk.choices[0].delta.content
            except Exception:
                text = None
            if text:
                yield f"data: {text}\n\n"
        yield "data: [DONE]\n\n"

    return _generator()


def get_response(
    system_prompt: str,
    messages: list[dict],
    max_tokens: int = MAX_TOKENS,
) -> str:
    """Get a complete (non-streaming) response from Groq."""
    groq_messages = [{"role": "system", "content": system_prompt}] + messages

    response = _get_client().chat.completions.create(
        model=MODEL,
        max_tokens=max_tokens,
        messages=groq_messages,
        stream=False,
    )
    # response.choices[0].message.content may vary by SDK version
    try:
        return response.choices[0].message.content
    except Exception:
        return getattr(response.choices[0], "text", "")
