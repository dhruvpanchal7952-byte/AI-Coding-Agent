"""
Thin wrapper around the Mistral AI SDK shared by all agents.
Requires the MISTRAL_API_KEY environment variable to be set.
"""
from dotenv import load_dotenv
load_dotenv()  
import os
import re


from mistralai.client import Mistral

_client = None

MODEL = "mistral-small-latest"
_FALLBACK_MODELS = ["mistral-small-latest", "mistral-medium-latest", "mistral-large-latest"]


def get_client():
    global _client
    if _client is None:
        api_key = os.environ.get("MISTRAL_API_KEY")
        if not api_key:
            raise RuntimeError(
                "MISTRAL_API_KEY is not set. Export it before running main.py, e.g.\n"
                "  export MISTRAL_API_KEY=sk-...\n"
            )
        _client = Mistral(api_key=api_key)
    return _client

def _build_messages(prompt: str, system: str = "") -> list[dict]:
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    return messages

def _get_model_candidates() -> list[str]:
    candidates = []
    if MODEL:
        candidates.append(MODEL)
    for fallback in _FALLBACK_MODELS:
        if fallback not in candidates:
            candidates.append(fallback)
    return candidates

def _extract_text_from_response(response) -> str:
    if response is None:
        return ""
    if isinstance(response, str):
        return response

    if hasattr(response, "choices"):
        choices = getattr(response, "choices")
        if choices:
            first = choices[0]
            if isinstance(first, dict):
                message = first.get("message") or {}
                return message.get("content", "") or first.get("text", "")
            message = getattr(first, "message", None)
            if message is not None:
                content = getattr(message, "content", None)
                if content:
                    return content
            text = getattr(first, "text", None)
            if text:
                return text

    if hasattr(response, "text"):
        return response.text

    if isinstance(response, dict):
        choices = response.get("choices") or []
        if choices:
            return choices[0].get("text", "")
        if "output" in response:
            out = response.get("output")
            if isinstance(out, list):
                return "".join(
                    o.get("content", {}).get("text", "")
                    for o in out
                    if isinstance(o, dict)
                )

    return str(response)

def call_llm(prompt: str, system: str = "", max_tokens: int = 10000, temperature: float = 0.2) -> str:
    """Send a single-turn prompt to the model and return the text response."""
    client = get_client()
    messages = _build_messages(prompt, system)
    model_candidates = _get_model_candidates()
    last_error = None

    
    chat = getattr(client, "chat", None)
    complete = getattr(chat, "complete", None) if chat is not None else None
    if callable(complete):
        for model_name in model_candidates:
            try:
                response = complete(
                    model=model_name,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                return _extract_text_from_response(response)
            except Exception as exc:
                last_error = exc

  
    completions = getattr(chat, "completions", None) if chat is not None else None
    create = getattr(completions, "create", None) if completions is not None else None
    if callable(create):
        for model_name in model_candidates:
            try:
                response = create(
                    model=model_name,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                return _extract_text_from_response(response)
            except Exception as exc:
                last_error = exc

    
    for attr in ("generate", "create", "messages"):
        fn = getattr(client, attr, None)
        if callable(fn):
            try:
                result = fn(model=model_candidates[0], prompt=prompt, max_tokens=max_tokens, temperature=temperature)
                return _extract_text_from_response(result)
            except Exception as exc:
                last_error = exc
    if last_error is not None:
        raise RuntimeError(f"Unable to call LLM: {last_error}") from last_error
    raise RuntimeError("Unable to call LLM: the installed SDK's interface is unsupported by this wrapper.")


def extract_code_block(text: str) -> str:
    """Pull the first ```python ... ``` (or bare ```...```) block out of a response."""
    match = re.search(r"```(?:python)?\s*\n(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text.strip()  