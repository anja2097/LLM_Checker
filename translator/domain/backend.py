"""Entidad Backend y descubrimiento de backends disponibles."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from translator.config.env import get_env
from translator.config.settings import PROMPTS_DIR


@dataclass(frozen=True)
class Backend:
    name: str
    slug: str
    prompts_dir: Path

    def translated_path(self, source_path: Path) -> Path:
        """Ruta del fichero traducido (Kokkos fuerza extensión .cpp)."""
        ext = ".cpp" if self.slug == "kokkos" else source_path.suffix
        return source_path.with_name(f"{source_path.stem}_{self.slug}{ext}")

    def run_cmd(self, exe_path: Path) -> list[str]:
        """Comando para ejecutar el binario traducido."""
        if self.slug == "mpi":
            nprocs = get_env("MPI_PROCS", "4")
            return ["mpirun", "-np", nprocs, str(exe_path)]
        return [str(exe_path)]

    def run_serial_cmd(self, exe_path: Path) -> list[str]:
        return [str(exe_path)]

    def run_env(self) -> dict[str, str]:
        """Variables de entorno para ejecutar el binario traducido."""
        if self.slug == "kokkos":
            return {
                "OMP_PROC_BIND": "spread",
                "OMP_PLACES": "threads",
            }
        return {}


def discover_backends() -> dict[str, Backend]:
    """Escanea prompts/ y devuelve backends con translate.txt y fix_errors.txt."""
    backends: dict[str, Backend] = {}
    if not PROMPTS_DIR.is_dir():
        return backends
    for subdir in sorted(PROMPTS_DIR.iterdir()):
        if not subdir.is_dir():
            continue
        if (subdir / "translate.txt").exists() and (subdir / "fix_errors.txt").exists():
            name = subdir.name
            backends[name.lower()] = Backend(
                name=name,
                slug=name.lower(),
                prompts_dir=subdir,
            )
    return backends


_BACKENDS: dict[str, Backend] = {}


def resolve_backend(name: str) -> Backend:
    """Resuelve un nombre (case-insensitive) al Backend correspondiente."""
    global _BACKENDS
    if not _BACKENDS:
        _BACKENDS = discover_backends()
    key = name.lower()
    if key in _BACKENDS:
        return _BACKENDS[key]
    known = ", ".join(b.name for b in _BACKENDS.values())
    raise ValueError(f"Backend desconocido: {name!r}. Usa uno de: {known}")
