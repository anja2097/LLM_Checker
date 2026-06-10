"""Fachada de compilación: despacha al toolchain del backend."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from translator.domain.backend import Backend
from translator.infrastructure.compilation import kokkos, mpi, openmp
from translator.infrastructure.compilation.common import executable_path


def compile_file(
    source_path: Path,
    backend: Backend,
    *,
    variant: Literal["translated", "serial"],
) -> tuple[bool, str]:
    if variant == "serial":
        return openmp.compile_openmp(source_path, serial=True)

    dispatch = {
        "openmp": lambda: openmp.compile_openmp(source_path, serial=False),
        "kokkos": lambda: kokkos.compile_kokkos(source_path),
        "mpi": lambda: mpi.compile_mpi(source_path),
    }
    compile_fn = dispatch.get(backend.slug)
    if compile_fn is None:
        raise ValueError(f"Backend sin toolchain de compilación: {backend.name!r}")
    return compile_fn()


__all__ = ["compile_file", "executable_path"]
