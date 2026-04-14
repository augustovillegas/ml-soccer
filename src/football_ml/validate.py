from __future__ import annotations

from argparse import ArgumentParser
from football_ml.export_notebook_cells import check_generated_markdown_sync
from importlib import import_module
import json
import subprocess
from pathlib import Path
import re
import sys
from typing import Iterable

import pandas as pd

from football_ml.config import load_ingestion_config
from football_ml.paths import (
    CONFIG_DIR,
    DATA_DIR,
    ManagedDataset,
    NOTEBOOK_DOCS_DIR,
    EXPECTED_KERNEL_DISPLAY_NAME,
    EXPECTED_KERNEL_NAME,
    EXPECTED_PYTHON,
    LOGS_DIR,
    PROJECT_ROOT,
    iter_managed_datasets,
    iter_managed_notebooks,
    relative_to_project,
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
REQUIRED_IMPORTS = ("soccerdata", "pandas", "pyarrow", "jupyter", "notebook", "pytest")
NOTEBOOK_FORBIDDEN_SNIPPETS = ("MatchHistory(", "read_games(")
MANAGED_NOTEBOOK_PATTERN = re.compile(r"^\d{2}_[a-z0-9]+(?:_[a-z0-9]+)*\.ipynb$")
CELL_ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
HEADING_PATTERN = re.compile(r"^# \d+\. .+")
VALID_DATASET_STAGES = {"bronze", "silver", "gold"}
BOOTSTRAP_REQUIRED_SNIPPETS = (
    "PROJECT_ROOT = Path.cwd().parent if Path.cwd().name == \"notebooks\" else Path.cwd()",
    "EXPECTED_PYTHON = (PROJECT_ROOT / \".venv\" / \"Scripts\" / \"python.exe\").resolve()",
    "Path(sys.executable).resolve() != EXPECTED_PYTHON",
    "pd.set_option(\"display.max_columns\", None)",
)


def _is_expected_python() -> bool:
    return Path(sys.executable).resolve() == EXPECTED_PYTHON.resolve()


def _iter_source_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in SOURCE_SUFFIXES:
            continue
        if any(part in EXCLUDED_PARTS or part.endswith(".egg-info") for part in path.parts):
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


def _local_notebook_checkpoint_issues() -> list[str]:
    issues: list[str] = []
    for checkpoint_dir in PROJECT_ROOT.rglob(".ipynb_checkpoints"):
        if not checkpoint_dir.is_dir():
            continue
        if ".venv" in checkpoint_dir.parts:
            continue
        relative_dir = relative_to_project(checkpoint_dir)
        checkpoint_files = sorted(path.name for path in checkpoint_dir.iterdir() if path.is_file())
        details = f" ({', '.join(checkpoint_files)})" if checkpoint_files else ""
        issues.append(
            f"{relative_dir}: los checkpoints locales de notebook no forman parte del flujo oficial y deben eliminarse{details}."
        )
    return issues


def _read_dataset_frame(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == ".parquet":
        return pd.read_parquet(path)
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path)
    raise ValueError(f"{path}: extension de dataset no soportada para validacion ({path.suffix}).")


def _validate_managed_dataset(dataset: ManagedDataset) -> list[str]:
    issues: list[str] = []

    if dataset.stage not in VALID_DATASET_STAGES:
        return [f"{dataset.dataset_id}: stage invalido '{dataset.stage}'."]

    stage_root = (DATA_DIR / dataset.stage).resolve()
    dataset_path = dataset.path.resolve()

    try:
        dataset_path.relative_to(stage_root)
    except ValueError:
        issues.append(
            f"{dataset.dataset_id}: el dataset debe vivir dentro de '{stage_root}' y no en '{dataset_path}'."
        )
        return issues

    if dataset.stage in {"silver", "gold"} and dataset_path.parent == stage_root and not dataset.allow_stage_root_file:
        issues.append(
            f"{dataset.dataset_id}: los datasets '{dataset.stage}' nuevos no deben vivir en la raiz de '{stage_root}'."
        )

    if dataset.allow_stage_root_file and not dataset.transition_note:
        issues.append(
            f"{dataset.dataset_id}: toda excepcion de dataset en raiz de stage debe tener transition_note."
        )

    if not dataset.path.exists():
        issues.append(f"{dataset.dataset_id}: falta el dataset oficial '{dataset.path}'.")
        return issues

    dataframe = _read_dataset_frame(dataset.path)
    missing_columns = [column for column in dataset.required_columns if column not in dataframe.columns]
    if missing_columns:
        issues.append(
            f"{dataset.dataset_id}: faltan columnas requeridas en '{relative_to_project(dataset.path)}': {missing_columns}."
        )

    missing_unique_columns = [column for column in dataset.unique_key if column not in dataframe.columns]
    if missing_unique_columns:
        issues.append(
            f"{dataset.dataset_id}: faltan columnas de unicidad en '{relative_to_project(dataset.path)}': {missing_unique_columns}."
        )
    elif dataset.unique_key:
        duplicates = int(dataframe.duplicated(list(dataset.unique_key)).sum())
        if duplicates:
            issues.append(
                f"{dataset.dataset_id}: se detectaron {duplicates} filas duplicadas por clave {dataset.unique_key}."
            )

    if dataframe.empty:
        issues.append(f"{dataset.dataset_id}: el dataset oficial '{relative_to_project(dataset.path)}' esta vacio.")

    return issues


def _check_managed_datasets() -> list[str]:
    issues: list[str] = []
    dataset_ids: list[str] = []
    dataset_paths: list[Path] = []

    for dataset in iter_managed_datasets():
        dataset_ids.append(dataset.dataset_id)
        dataset_paths.append(dataset.path.resolve())

        if not dataset.update_policy.strip():
            issues.append(f"{dataset.dataset_id}: update_policy no puede ser vacio.")
        issues.extend(_validate_managed_dataset(dataset))

    duplicate_ids = sorted({dataset_id for dataset_id in dataset_ids if dataset_ids.count(dataset_id) > 1})
    if duplicate_ids:
        issues.append(f"Los datasets oficiales no deben repetir dataset_id: {duplicate_ids}.")

    duplicate_paths = sorted(
        {
            str(relative_to_project(path))
            for path in dataset_paths
            if dataset_paths.count(path) > 1
        }
    )
    if duplicate_paths:
        issues.append(f"Los datasets oficiales no deben repetir path: {duplicate_paths}.")

    return issues


def _git_tracked_paths() -> list[str]:
    tracked_result = subprocess.run(
        ["git", "ls-files"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if tracked_result.returncode != 0:
        return []
    deleted_result = subprocess.run(
        ["git", "diff", "--name-only", "--cached", "--diff-filter=D"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    deleted_paths = {
        line.strip().replace("\\", "/")
        for line in deleted_result.stdout.splitlines()
        if line.strip()
    }
    return [
        line.strip().replace("\\", "/")
        for line in tracked_result.stdout.splitlines()
        if line.strip() and line.strip().replace("\\", "/") not in deleted_paths
    ]


def _allowed_tracked_data_paths() -> set[str]:
    config = load_ingestion_config()
    allowed_paths = {
        str(relative_to_project(dataset.path)).replace("\\", "/")
        for dataset in iter_managed_datasets()
    }
    for season in config.seasons:
        allowed_paths.add(str(relative_to_project(config.canonical_csv_path(season))).replace("\\", "/"))
        allowed_paths.add(str(relative_to_project(config.manifest_path(season))).replace("\\", "/"))
    return allowed_paths


def _tracked_generated_artifact_issues(
    tracked_paths: Iterable[str],
    allowed_data_paths: set[str] | None = None,
) -> list[str]:
    issues: list[str] = []
    effective_allowed_data_paths = allowed_data_paths if allowed_data_paths is not None else _allowed_tracked_data_paths()

    for tracked_path in tracked_paths:
        if "/.ipynb_checkpoints/" in tracked_path or tracked_path.startswith(".ipynb_checkpoints/"):
            issues.append(
                f"{tracked_path}: los checkpoints de notebook no deben estar versionados."
            )
        if ".egg-info/" in tracked_path:
            issues.append(f"{tracked_path}: '*.egg-info/' es un artefacto generado y no debe estar versionado.")
        if "/.pytest_cache/" in tracked_path or tracked_path.startswith(".pytest_cache/"):
            issues.append(f"{tracked_path}: '.pytest_cache/' es un artefacto generado y no debe estar versionado.")
        if (
            tracked_path.startswith("data/")
            and not tracked_path.endswith(".gitkeep")
            and tracked_path not in effective_allowed_data_paths
        ):
            issues.append(
                f"{tracked_path}: solo los datasets y artefactos oficiales de data registrados para distribucion pueden quedar versionados."
            )
        if tracked_path.startswith("logs/") and not tracked_path.endswith(".gitkeep"):
            issues.append(
                f"{tracked_path}: los artefactos de logs no deben estar versionados salvo '.gitkeep'."
            )

    return issues


def _check_tracked_generated_artifacts() -> list[str]:
    return _tracked_generated_artifact_issues(_git_tracked_paths())


def _check_notebook() -> list[str]:
    issues: list[str] = []
    for entry in iter_managed_notebooks():
        if not entry.notebook_path.exists():
            issues.append(f"Falta la ruta requerida: {entry.notebook_path}")
            continue

        notebook = json.loads(entry.notebook_path.read_text(encoding="utf-8"))
        kernelspec = notebook.get("metadata", {}).get("kernelspec", {})
        raw_cells = notebook.get("cells", [])
        code_cells = [cell for cell in raw_cells if isinstance(cell, dict) and cell.get("cell_type") == "code"]

        if kernelspec.get("name") != EXPECTED_KERNEL_NAME:
            issues.append(
                f"{entry.notebook_path}: kernelspec.name debe ser '{EXPECTED_KERNEL_NAME}' y no '{kernelspec.get('name')}'."
            )
        if kernelspec.get("display_name") != EXPECTED_KERNEL_DISPLAY_NAME:
            issues.append(
                f"{entry.notebook_path}: kernelspec.display_name debe ser '{EXPECTED_KERNEL_DISPLAY_NAME}'."
            )
        if not MANAGED_NOTEBOOK_PATTERN.match(entry.notebook_path.name):
            issues.append(
                f"{entry.notebook_path}: el nombre del notebook debe seguir el patron 'NN_<etapa>_<tema>.ipynb'."
            )
        if not code_cells:
            issues.append(f"{entry.notebook_path}: el notebook debe tener al menos una celda de codigo.")
            continue

        actual_cell_ids = tuple(str(cell.get("id", "")).strip() for cell in code_cells)
        if actual_cell_ids != entry.expected_cell_ids:
            issues.append(
                f"{entry.notebook_path}: los ids de celda deben ser {entry.expected_cell_ids} y no {actual_cell_ids}."
            )

        invalid_ids = [cell_id for cell_id in actual_cell_ids if not CELL_ID_PATTERN.match(cell_id)]
        if invalid_ids:
            issues.append(
                f"{entry.notebook_path}: todos los ids de celda deben ser slugs descriptivos y estables ({invalid_ids})."
            )
        if len(set(actual_cell_ids)) != len(actual_cell_ids):
            issues.append(f"{entry.notebook_path}: los ids de celda no deben repetirse.")

        for index, cell in enumerate(code_cells, start=1):
            source = cell.get("source", [])
            source_text = "".join(source) if isinstance(source, list) else str(source)
            lines = [line.strip() for line in source_text.splitlines() if line.strip()]

            if len(lines) < 3:
                issues.append(
                    f"{entry.notebook_path}: la celda {index} debe incluir encabezado numerado estilo notebook 01."
                )
                continue

            if not (
                lines[0].startswith("#")
                and set(lines[0].replace("#", "").strip()) <= {"="}
                and HEADING_PATTERN.match(lines[1])
                and lines[2].startswith("#")
                and set(lines[2].replace("#", "").strip()) <= {"="}
            ):
                issues.append(
                    f"{entry.notebook_path}: la celda {index} debe empezar con separador, titulo numerado y separador."
                )

        first_source = code_cells[0].get("source", [])
        first_cell_text = "".join(first_source) if isinstance(first_source, list) else str(first_source)
        for snippet in BOOTSTRAP_REQUIRED_SNIPPETS:
            if snippet not in first_cell_text:
                issues.append(
                    f"{entry.notebook_path}: la primera celda debe incluir el bootstrap comun del proyecto ({snippet})."
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
            PROJECT_ROOT / "tests",
            PROJECT_ROOT / "docs" / "guides" / "reglas-escalado-seguro.md",
            *managed_paths,
        ):
            if not path.exists():
                issues.append(f"Falta la ruta requerida: {path}")
        issues.extend(_check_managed_datasets())
        issues.extend(_check_tracked_generated_artifacts())
        issues.extend(_local_notebook_checkpoint_issues())
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
