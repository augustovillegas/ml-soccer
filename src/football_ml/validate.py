from __future__ import annotations

from argparse import ArgumentParser
from football_ml.export_notebook_cells import check_generated_markdown_sync
from importlib import import_module
import json
from pathlib import Path
import sys
from typing import Iterable

from football_ml.config import load_ingestion_config
from football_ml.paths import (
    CONFIG_DIR,
    DATA_DIR,
    NOTEBOOK_DOCS_DIR,
    EXPECTED_KERNEL_DISPLAY_NAME,
    EXPECTED_KERNEL_NAME,
    EXPECTED_PYTHON,
    LOGS_DIR,
    PROJECT_ROOT,
    iter_managed_notebooks,
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
    for entry in iter_managed_notebooks():
        if not entry.notebook_path.exists():
            issues.append(f"Falta la ruta requerida: {entry.notebook_path}")
            continue

        notebook = json.loads(entry.notebook_path.read_text(encoding="utf-8"))
        kernelspec = notebook.get("metadata", {}).get("kernelspec", {})

        if kernelspec.get("name") != EXPECTED_KERNEL_NAME:
            issues.append(
                f"{entry.notebook_path}: kernelspec.name debe ser '{EXPECTED_KERNEL_NAME}' y no '{kernelspec.get('name')}'."
            )
        if kernelspec.get("display_name") != EXPECTED_KERNEL_DISPLAY_NAME:
            issues.append(
                f"{entry.notebook_path}: kernelspec.display_name debe ser '{EXPECTED_KERNEL_DISPLAY_NAME}'."
            )

        notebook_text = entry.notebook_path.read_text(encoding="utf-8")
        for snippet in NOTEBOOK_FORBIDDEN_SNIPPETS:
            if snippet in notebook_text:
                issues.append(f"{entry.notebook_path}: el notebook no debe hacer ingesta online ({snippet}).")
    return issues


def _check_generated_notebook_doc() -> list[str]:
    issues: list[str] = []

    for entry in iter_managed_notebooks():
        if not entry.notebook_path.exists():
            continue
        issues.extend(check_generated_markdown_sync(entry.notebook_path, entry.doc_path))

    return issues


def _check_required_paths(config) -> list[str]:
    issues: list[str] = []
    required_paths = [
        PROJECT_ROOT / ".gitignore",
        PROJECT_ROOT / "pyproject.toml",
        PROJECT_ROOT / "requirements.txt",
        CONFIG_DIR / "ingestion.toml",
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
    return issues


def parse_args() -> ArgumentParser:
    parser = ArgumentParser(description="Valida la configuracion estructural del proyecto football-ml.")
    parser.add_argument(
        "--scope",
        choices=("project", "runtime"),
        default="project",
        help="Scope 'project' valida tambien notebook y archivos fuente. Scope 'runtime' valida solo entorno/configuracion operativa.",
    )
    return parser


def main() -> int:
    args = parse_args().parse_args()
    issues: list[str] = []

    if not _is_expected_python():
        issues.append(f"El interprete activo es '{sys.executable}' y no '{EXPECTED_PYTHON}'.")

    for module_name in REQUIRED_IMPORTS:
        try:
            import_module(module_name)
        except Exception as exc:  # pragma: no cover - import error path
            issues.append(f"No se pudo importar '{module_name}': {exc}")

    config = load_ingestion_config()
    issues.extend(_check_required_paths(config))

    if KERNELSPEC_PATH.exists():
        kernel_payload = json.loads(KERNELSPEC_PATH.read_text(encoding="utf-8"))
        if kernel_payload.get("display_name") != EXPECTED_KERNEL_DISPLAY_NAME:
            issues.append(
                f"{KERNELSPEC_PATH}: display_name debe ser '{EXPECTED_KERNEL_DISPLAY_NAME}'."
            )

    if args.scope == "project":
        managed_paths = []
        for entry in iter_managed_notebooks():
            managed_paths.extend((entry.notebook_path, entry.doc_path))
        for path in (
            PROJECT_ROOT / "AGENTS.md",
            PROJECT_ROOT / "BITACORA_ENTORNO.md",
            NOTEBOOK_DOCS_DIR,
            *managed_paths,
        ):
            if not path.exists():
                issues.append(f"Falta la ruta requerida: {path}")
        issues.extend(_check_notebook())
        issues.extend(_check_generated_notebook_doc())
        issues.extend(_check_mojibake())

    if issues:
        print("Project validation failed:")
        for issue in issues:
            print(f"- {issue}")
        return 1

    print("Project validation passed.")
    print(f"- Scope: {args.scope}")
    print(f"- Python: {sys.executable}")
    print(f"- Kernel: {EXPECTED_KERNEL_DISPLAY_NAME}")
    print(f"- MatchHistory raw dir: {config.raw_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
