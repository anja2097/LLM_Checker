"""Ejecución y verificación de programas serial vs traducido."""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

from translator.config.settings import BENCHMARK_RUNS, EXECUTION_TIMEOUT_SECONDS
from translator.domain.backend import Backend
from translator.infrastructure.compilation import compile_file, executable_path


def _format_execute_cmd(cmd: list[str], env: dict[str, str] | None = None) -> str:
    parts = [f"{key}={value}" for key, value in (env or {}).items()]
    parts.extend(cmd)
    return " ".join(parts)


def _print_execute(
    label: str,
    cmd: list[str],
    runs: int,
    *,
    env: dict[str, str] | None = None,
) -> None:
    print(f"\n\n  Ejecutando ({label}): {_format_execute_cmd(cmd, env)}")
    print(f"  Límite por ejecución: {EXECUTION_TIMEOUT_SECONDS} s")
    if runs > 1:
        print(f"  Repeticiones: {runs}")


def _run_once(
    exe_path: Path,
    cmd: list[str],
    env: dict[str, str] | None = None,
) -> tuple[str, str, float]:
    run_env = os.environ.copy()
    if env:
        run_env.update(env)

    start = time.perf_counter()
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=exe_path.parent,
            env=run_env,
            timeout=EXECUTION_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        print("  Resultado: tiempo de ejecución agotado")
        print(
            f"[ERROR] La ejecución superó {EXECUTION_TIMEOUT_SECONDS} s: {exe_path}"
        )
        print("        Posible bucle infinito o programa demasiado lento.")
        sys.exit(1)
    elapsed = time.perf_counter() - start

    if result.returncode != 0:
        print("  Resultado: error de ejecución")
        print(f"[ERROR] El ejecutable falló: {exe_path}")
        print(result.stderr or result.stdout)
        sys.exit(1)

    return result.stdout, result.stderr, elapsed


def _benchmark(
    exe_path: Path,
    cmd: list[str],
    runs: int,
    *,
    label: str,
    env: dict[str, str] | None = None,
) -> tuple[str, str, float]:
    _print_execute(label, cmd, runs, env=env)
    stdout, stderr, total = "", "", 0.0
    for _ in range(runs):
        stdout, stderr, elapsed = _run_once(exe_path, cmd, env=env)
        total += elapsed
    print("  Resultado: ejecución OK")
    return stdout, stderr, total / runs


def verify_and_benchmark(original_path: Path, backend: Backend) -> None:
    """Compila y ejecuta el original (serial) y la versión traducida."""
    translated_path = backend.translated_path(original_path)
    serial_exe = executable_path(original_path)
    translated_exe = executable_path(translated_path)

    print(f"\n\n{'=' * 50}")
    print(f"  Verificación: serial vs {backend.name}")
    print(f"{'=' * 50}")

    print("\n\n  Compilando versión serial…")
    ok, err = compile_file(original_path, backend, variant="serial")
    if not ok:
        print("[ERROR] No se pudo compilar el fichero original:")
        print(err)
        sys.exit(1)

    runs = BENCHMARK_RUNS
    serial_cmd = backend.run_serial_cmd(serial_exe)
    translated_cmd = backend.run_cmd(translated_exe)

    serial_stdout, serial_stderr, serial_time = _benchmark(
        serial_exe, serial_cmd, runs, label="serial",
    )

    trans_stdout, trans_stderr, trans_time = _benchmark(
        translated_exe,
        translated_cmd,
        runs,
        label=backend.name,
        env=backend.run_env(),
    )

    print(f"\n\n{'-' * 50}")
    print("  Comparación de salida")
    print(f"{'-' * 50}")

    stdout_match = serial_stdout == trans_stdout
    stderr_match = serial_stderr == trans_stderr

    if stdout_match and stderr_match:
        print("  Salida idéntica (stdout y stderr)")
    else:
        print("  [AVISO] Las salidas difieren:")
        if not stdout_match:
            print("     stdout: distinto")
            print(f"     serial:    {serial_stdout!r}")
            print(f"     {backend.slug}: {trans_stdout!r}")
        if not stderr_match:
            print("     stderr: distinto")
            print(f"     serial:    {serial_stderr!r}")
            print(f"     {backend.slug}: {trans_stderr!r}")

    print(f"\n\n{'-' * 50}")
    print("  Tiempos de ejecución")
    print(f"{'-' * 50}")
    print(f"  Serial      (media de {runs}): {serial_time * 1000:.3f} ms")
    print(f"  {backend.name:<10} (media de {runs}): {trans_time * 1000:.3f} ms")

    if trans_time > 0:
        speedup = serial_time / trans_time
        print(f"  Speedup: {speedup:.2f}x")
        if speedup < 1.0:
            print("  (El paralelo es más lento — normal en programas muy pequeños)")
    else:
        print("  Speedup: N/A (tiempo traducido ~ 0)")

    print(f"\n{'=' * 50}\n")
