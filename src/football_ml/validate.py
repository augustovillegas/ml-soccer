from __future__ import annotations

from importlib import import_module
import json
from pathlib import Path
import sys
from typing import Iterable

from football_ml.config import load_ingestion_config
from football_ml.paths import (
    CONFIG_DIR,
    DATA_DIR,
    EXPECTED_KERNEL_DISPLAY_NAME,
    EXPECTED_KERNEL_NAME,
    EXPECTED_PYTHON,
    LOGS_DIR,
    NOTEBOOK_PATH,
    PROJECT_ROOT,
)


KERNELSPEC_PATH = PROJECT_ROOT / ".venv" / "share" / "jupyter" / "kernels" / EXPECTED_KERNEL_NAME / "kernel.json"
SOURCE_SUFFIXES = {".md", ".py", ".ps1", ".toml", ".ipynb", ".json", ".txt"}
EXCLUDED_PARTS = {".git", ".venv", "__pycache__", ".ipynb_checkpoints", "data", "logs"}
SUSPICIOUS_SEQUENCES = (
    "\u00c3",
    "\u00c2",
    "\ufffd",
    "\u00ef\u00bb\u00bf",
    "\u00ee\u02c6\u20ac",
    "\u00e2\u20ac\u201d",
    "\u00e2\u20ac\u201c",
    "\u00e2\u20ac\u2122",
    "\u00e2\u20ac\u0153",
    "\u00e2\u20ac",
)
REQUIRED_IMPORTS = ("soccerdata", "pandas", "pyarrow", "jupyter", "notebook")
NOTEBOOK_FORBIDDEN_SNIPPETS = ("MatchHistory(", "read_games(")


def _is_expected_python() -> bool:
    return Path(sys.executable).resolve() == EXPECTED_PYTHON.resolve()


def _iter_source_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in SOURCE_SUFFIXES:
            continue
        if any(part in EXCLUDED_PARTS for part in path.parts):
            continue
        yield path


def _check_mojibake() -> list[str]:
    issues: list[str] = []
    for path in _iter_source_files(PROJECT_ROOT):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            issues.append(f"{path}: no se pudo leer como UTF-8 ({exc}).")
            continue
        matches = [sequence for sequence in SUSPICIOUS_SEQUENCES if sequence in text]
        if matches:
            issues.append(f"{path}: secuencias sospechosas de mojibake detectadas ({', '.join(matches)}).")
    return issues


def _check_notebook() -> list[str]:
    issues: list[str] = []
    notebook = json.loads(NOTEBOOK_PATH.read_text(encoding="utf-8"))
    kernelspec = notebook.get("metadata", {}).get("kernelspec", {})

    if kernelspec.get("name") != EXPECTED_KERNEL_NAME:
        issues.append(
            f"{NOTEBOOK_PATH}: kernelspec.name debe ser '{EXPECTED_KERNEL_NAME}' y no '{kernelspec.get('name')}'."
        )
    if kernelspec.get("display_name") != EXPECTED_KERNEL_DISPLAY_NAME:
        issues.append(
            f"{NOTEBOOK_PATH}: kernelspec.display_name debe ser '{EXPECTED_KERNEL_DISPLAY_NAME}'."
        )

    notebook_text = NOTEBOOK_PATH.read_text(encoding="utf-8")
    for snippet in NOTEBOOK_FORBIDDEN_SNIPPETS:
        if snippet in notebook_text:
            issues.append(f"{NOTEBOOK_PATH}: el notebook no debe hacer ingesta online ({snippet}).")
    return issues


def main() -> int:
    issues: list[str] = []

    if not _is_expected_python():
        issues.append(f"El interprete activo es '{sys.executable}' y no '{EXPECTED_PYTHON}'.")

    for module_name in REQUIRED_IMPORTS:
        try:
            import_module(module_name)
        except Exception as exc:  # pragma: no cover - import error path
            issues.append(f"No se pudo importar '{module_name}': {exc}")

    config = load_ingestion_config()

    required_paths = [
        PROJECT_ROOT / ".gitignore",
        PROJECT_ROOT / "requirements.txt",
        PROJECT_ROOT / "AGENTS.md",
        PROJECT_ROOT / "BITACORA_ENTORNO.md",
        CONFIG_DIR / "ingestion.toml",
        NOTEBOOK_PATH,
        KERNELSPEC_PATH,
        DATA_DIR / "bronze",
        DATA_DIR / "silver",
        DATA_DIR / "gold",
        LOGS_DIR / "ingestion",
        *config.iter_required_dirs(),
    ]
    for path in required_paths:
        if not path.exists():
            issues.append(f"Falta la ruta requerida: {path}")

    if KERNELSPEC_PATH.exists():
        kernel_payload = json.loads(KERNELSPEC_PATH.read_text(encoding="utf-8"))
        if kernel_payload.get("display_name") != EXPECTED_KERNEL_DISPLAY_NAME:
            issues.append(
                f"{KERNELSPEC_PATH}: display_name debe ser '{EXPECTED_KERNEL_DISPLAY_NAME}'."
            )

    issues.extend(_check_notebook())
    issues.extend(_check_mojibake())

    if issues:
        print("Project validation failed:")
        for issue in issues:
            print(f"- {issue}")
        return 1

    print("Project validation passed.")
    print(f"- Python: {sys.executable}")
    print(f"- Kernel: {EXPECTED_KERNEL_DISPLAY_NAME}")
    print(f"- MatchHistory raw dir: {config.raw_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
