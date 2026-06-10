"""Utilidades compartidas para compilación C/C++."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


def resolve_c_compiler(source_path: Path, *, cxx: bool = False) -> str:
    if cxx or source_path.suffix == ".cpp":
        candidates = ["g++", "g++-15"]
    else:
        candidates = ["gcc", "gcc-15"]
    for c in candidates:
        if shutil.which(c):
            return c
    print("[ERROR] No se encontró compilador C/C++ en PATH.")
    sys.exit(1)


def run_compile(cmd: list[str], *, label: str) -> tuple[bool, str]:
    print(f"\n\n  Compilando ({label}): {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    output = (result.stdout + result.stderr).strip()
    if result.returncode == 0:
        print("  Resultado: compilación OK")
        return True, ""
    print("  Resultado: error de compilación")
    return False, output


def executable_path(source_path: Path) -> Path:
    return source_path.with_suffix("")
