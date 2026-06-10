"""Caso de uso: traducción serial → backend paralelo con corrección iterativa."""

from __future__ import annotations

import sys
from pathlib import Path

from translator.config.settings import MAX_RETRIES
from translator.domain.backend import Backend
from translator.infrastructure.compilation import compile_file
from translator.infrastructure.execution.runner import verify_and_benchmark
from translator.infrastructure.llm.openrouter import (
    chat_completion,
    extract_content,
    extract_message,
)


def _load_prompt(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _assistant_turn(message: dict) -> dict:
    turn: dict = {
        "role": "assistant",
        "content": message.get("content"),
    }
    if message.get("reasoning_details") is not None:
        turn["reasoning_details"] = message["reasoning_details"]
    return turn


def _write_source(target_path: Path, code: str) -> None:
    target_path.write_text(code, encoding="utf-8")
    print(f"  Fichero actualizado: {target_path}")


def _on_compile_success(original_path: Path, backend: Backend, iteration: int) -> None:
    print(f"\n\nCompilado correctamente en la iteración {iteration}.")
    verify_and_benchmark(original_path, backend)


def translate_file(
    source_path: Path,
    api_key: str,
    *,
    backend: Backend,
    model: str,
    thinking: bool = False,
    thinking_effort: str | None = None,
) -> None:
    """Traduce un fichero serial al backend indicado, corrigiendo errores de compilación."""
    translated_path = backend.translated_path(source_path)
    source_code = source_path.read_text(encoding="utf-8")
    translate_prompt = _load_prompt(backend.prompts_dir / "translate.txt")
    fix_prompt = _load_prompt(backend.prompts_dir / "fix_errors.txt")

    print(f"\n\n  Original:  {source_path}")
    print(f"  Traducido: {translated_path}\n")

    user_msg = {"role": "user", "content": f"{translate_prompt}\n\n{source_code}"}
    messages: list[dict] = [user_msg]

    llm_kwargs = {
        "model": model,
        "thinking": thinking,
        "thinking_effort": thinking_effort,
    }

    data = chat_completion(
        api_key,
        messages,
        label="Iteración 1 — traducción inicial",
        **llm_kwargs,
    )
    assistant_msg = extract_message(data)
    messages.append(_assistant_turn(assistant_msg))

    translated_code = extract_content(data)
    _write_source(translated_path, translated_code)

    ok, error_output = compile_file(translated_path, backend, variant="translated")
    if ok:
        _on_compile_success(source_path, backend, 1)
        return

    for iteration in range(2, MAX_RETRIES + 1):
        current_code = translated_path.read_text(encoding="utf-8")
        fix_user_content = (
            f"{fix_prompt}\n\n{current_code}\n\nCompilation errors:\n{error_output}"
        )
        messages.append({"role": "user", "content": fix_user_content})

        data = chat_completion(
            api_key,
            messages,
            label=f"Iteración {iteration} — corrección de errores",
            **llm_kwargs,
        )
        assistant_msg = extract_message(data)
        messages.append(_assistant_turn(assistant_msg))

        translated_code = extract_content(data)
        _write_source(translated_path, translated_code)

        ok, error_output = compile_file(translated_path, backend, variant="translated")
        if ok:
            _on_compile_success(source_path, backend, iteration)
            return

    print(f"\n\n[ERROR] No se pudo compilar tras {MAX_RETRIES} iteraciones. Último error:")
    print(error_output)
    sys.exit(1)
