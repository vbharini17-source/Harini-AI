import asyncio
from typing import TypeVar

from pydantic import BaseModel

from config import settings

Schema = TypeVar("Schema", bound=BaseModel)


class GeminiNotConfiguredError(RuntimeError):
    pass


class GeminiRequestError(RuntimeError):
    def __init__(self, message: str, *, status_code: int = 502):
        super().__init__(message)
        self.status_code = status_code


def _to_request_error(exc: Exception) -> GeminiRequestError:
    status_code = getattr(exc, "code", None)
    if status_code == 503:
        return GeminiRequestError(
            "Gemini is temporarily busy. Please try again in a minute.",
            status_code=503,
        )
    if status_code == 429:
        return GeminiRequestError(
            "Gemini is receiving too many requests. Please wait a moment and try again.",
            status_code=429,
        )
    if status_code in {401, 403}:
        return GeminiRequestError(
            "Gemini rejected the request. Check the API key and model access.",
            status_code=502,
        )

    message = getattr(exc, "message", None) or str(exc).strip()
    if settings.gemini_api_key:
        message = message.replace(settings.gemini_api_key, "[redacted]")
    if not message:
        message = type(exc).__name__
    return GeminiRequestError(f"Gemini request failed: {message[:500]}")


def _load_sdk():
    try:
        from google import genai
        from google.genai import types
    except ImportError as exc:
        raise RuntimeError(
            "Google GenAI SDK is missing. Install project requirements first."
        ) from exc
    return genai, types


def _get_client():
    if not settings.gemini_api_key:
        raise GeminiNotConfiguredError(
            "GEMINI_API_KEY is not configured. Add it to your .env file."
        )
    genai, _ = _load_sdk()
    return genai.Client(api_key=settings.gemini_api_key)


async def _generate_content(client, **kwargs):
    try:
        return await asyncio.to_thread(
            client.models.generate_content,
            **kwargs,
        )
    except Exception as exc:
        fallback_model = settings.gemini_fallback_model
        if (
            getattr(exc, "code", None) == 503
            and fallback_model
            and fallback_model != kwargs.get("model")
        ):
            try:
                fallback_kwargs = {**kwargs, "model": fallback_model}
                return await asyncio.to_thread(
                    client.models.generate_content,
                    **fallback_kwargs,
                )
            except Exception as fallback_exc:
                raise _to_request_error(fallback_exc) from fallback_exc
        raise _to_request_error(exc) from exc


async def generate_text(
    prompt: str,
    *,
    system_instruction: str,
    temperature: float = 0.3,
    max_output_tokens: int = 1200,
) -> str:
    _, types = _load_sdk()
    client = _get_client()
    config = types.GenerateContentConfig(
        temperature=temperature,
        max_output_tokens=max_output_tokens,
        system_instruction=system_instruction,
    )
    response = await _generate_content(
        client,
        model=settings.gemini_model,
        contents=prompt,
        config=config,
    )
    text = (response.text or "").strip()
    if not text:
        raise RuntimeError("Gemini returned an empty response.")
    return text


async def generate_structured(
    prompt: str,
    schema: type[Schema],
    *,
    system_instruction: str,
    temperature: float = 0.2,
    max_output_tokens: int = 1800,
) -> Schema:
    _, types = _load_sdk()
    client = _get_client()
    config = types.GenerateContentConfig(
        temperature=temperature,
        max_output_tokens=max_output_tokens,
        system_instruction=system_instruction,
        response_mime_type="application/json",
        response_schema=schema,
    )
    response = await _generate_content(
        client,
        model=settings.gemini_model,
        contents=prompt,
        config=config,
    )
    text = (response.text or "").strip()
    if not text:
        raise RuntimeError("Gemini returned an empty response.")
    return schema.model_validate_json(text)