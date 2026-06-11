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
    extra_flags: list[str] | None = None,
) -> tuple[bool, str]:
    extra = extra_flags or []
    if variant == "serial":
        return openmp.compile_openmp(source_path, serial=True, extra_flags=extra)

    dispatch = {
        "openmp": lambda: openmp.compile_openmp(
            source_path, serial=False, extra_flags=extra,
        ),
        "kokkos": lambda: kokkos.compile_kokkos(source_path, extra_flags=extra),
        "mpi": lambda: mpi.compile_mpi(source_path, extra_flags=extra),
    }
    compile_fn = dispatch.get(backend.slug)
    if compile_fn is None:
        raise ValueError(f"Backend sin toolchain de compilación: {backend.name!r}")
    return compile_fn()


__all__ = ["compile_file", "executable_path"]
