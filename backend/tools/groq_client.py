from groq import Groq
import os
from typing import AsyncGenerator

# Initialize the Groq client
# API key is read from GROQ_API_KEY environment variable
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

MODEL = "llama-3.3-70b-versatile"  # Fast, capable model on Groq
MAX_TOKENS = 4096


def stream_response(
    system_prompt: str,
    messages: list[dict],
    max_tokens: int = MAX_TOKENS,
):
    """Stream a response from Groq as server-sent events."""
    groq_messages = [{"role": "system", "content": system_prompt}] + messages

    stream = client.chat.completions.create(
        model=MODEL,
        max_tokens=max_tokens,
        messages=groq_messages,
        stream=True,
    )

    def _generator():
        for chunk in stream:
            text = chunk.choices[0].delta.content
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

    response = client.chat.completions.create(
        model=MODEL,
        max_tokens=max_tokens,
        messages=groq_messages,
        stream=False,
    )
    return response.choices[0].message.content
