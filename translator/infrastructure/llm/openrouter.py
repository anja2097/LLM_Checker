"""Cliente HTTP para la API de OpenRouter."""

import json
import sys

import requests

from translator.config.settings import API_URL


def _api_headers(api_key: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


def _reasoning_payload(*, thinking: bool, effort: str | None) -> dict | None:
    if not thinking:
        return None
    reasoning: dict = {"enabled": True}
    if effort is not None:
        reasoning["effort"] = effort
    return reasoning


def chat_completion(
    api_key: str,
    messages: list[dict],
    *,
    model: str,
    thinking: bool = False,
    thinking_effort: str | None = None,
    label: str = "",
) -> dict:
    payload: dict = {
        "model": model,
        "messages": messages,
    }
    reasoning = _reasoning_payload(thinking=thinking, effort=thinking_effort)
    if reasoning is not None:
        payload["reasoning"] = reasoning

    if label:
        print(f"\n\n{'-' * 50}")
        print(f"  {label}")
        print(f"{'-' * 50}")

    response = requests.post(
        API_URL,
        headers=_api_headers(api_key),
        json=payload,
        timeout=120,
    )

    print(f"\nHTTP {response.status_code}")

    try:
        data = response.json()
    except json.JSONDecodeError:
        print("Respuesta no JSON:")
        print(response.text[:500])
        sys.exit(1)

    if not response.ok:
        print("Error de API:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        sys.exit(1)

    return data


def _resolve_message_text(message: dict) -> str:
    """Obtiene el texto de la respuesta; algunos modelos dejan content=null."""
    content = message.get("content")
    if isinstance(content, str) and content.strip():
        return content

    for key in ("reasoning", "reasoning_content"):
        value = message.get(key)
        if isinstance(value, str) and value.strip():
            return value

    details = message.get("reasoning_details")
    if isinstance(details, list):
        for item in reversed(details):
            if not isinstance(item, dict):
                continue
            if item.get("type") == "reasoning.text":
                text = item.get("text")
                if isinstance(text, str) and text.strip():
                    return text

    return ""


def strip_code_fences(content: str | None) -> str:
    """Elimina la primera y última línea si el LLM envuelve el código en ```."""
    if not content:
        return ""
    lines = content.splitlines()
    if not lines or not lines[0].strip().startswith("```"):
        return content
    if len(lines) >= 2 and lines[-1].strip().startswith("```"):
        return "\n".join(lines[1:-1])
    return "\n".join(lines[1:])


def strip_leading_until_hash(content: str) -> str:
    """Elimina líneas iniciales hasta la primera que empiece por '#'."""
    lines = content.splitlines()
    while lines and not lines[0].lstrip().startswith("#"):
        lines.pop(0)
    return "\n".join(lines)


def strip_trailing_fence(content: str) -> str:
    """Elimina una línea final de cierre ``` si quedó tras el recorte."""
    lines = content.splitlines()
    if lines and lines[-1].strip().startswith("```"):
        lines.pop()
    return "\n".join(lines)


def extract_code(content: str | None) -> str:
    code = strip_code_fences(content)
    code = strip_leading_until_hash(code)
    return strip_trailing_fence(code)


def extract_content(data: dict) -> str:
    message = data["choices"][0]["message"]
    raw = _resolve_message_text(message)
    if not raw:
        print("[ERROR] El modelo devolvió una respuesta vacía (content=null).")
        print("        Prueba otro modelo o reintenta la traducción.")
        sys.exit(1)
    return extract_code(raw)


def extract_message(data: dict) -> dict:
    return data["choices"][0]["message"]
