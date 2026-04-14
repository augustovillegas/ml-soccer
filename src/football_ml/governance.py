from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
import tomllib


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = PROJECT_ROOT / "config"
PROJECT_GOVERNANCE_PATH = CONFIG_DIR / "project_governance.toml"
SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:_[a-z0-9]+)*$")


@dataclass(frozen=True)
class GovernedEnvironment:
    python_version: str
    kernel_name: str
    kernel_display_name: str
    notebooks_dir: Path
    notebook_docs_dir: Path


@dataclass(frozen=True)
class ManagedNotebook:
    notebook_id: str
    order: int
    stage: str
    topic: str
    notebook_path: Path
    doc_path: Path
    template_profile: str
    source_dataset_ids: tuple[str, ...]
    output_dataset_ids: tuple[str, ...]


@dataclass(frozen=True)
class ProjectGovernance:
    project_root: Path
    config_path: Path
    environment: GovernedEnvironment
    notebooks: tuple[ManagedNotebook, ...]


def slugify_token(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", value.lower())
    return slug.strip("_")


def _resolve_project_path(raw_path: str, project_root: Path) -> Path:
    path = Path(raw_path)
    if path.is_absolute():
        return path
    return project_root / path


def _ensure_slug(value: str, field_name: str) -> str:
    if not SLUG_PATTERN.match(value):
        raise ValueError(
            f"{field_name} debe ser un slug en snake_case con solo letras minusculas, numeros y '_' ({value!r})."
        )
    return value


def _load_environment(raw_environment: dict[str, object], project_root: Path) -> GovernedEnvironment:
    return GovernedEnvironment(
        python_version=str(raw_environment["python_version"]),
        kernel_name=str(raw_environment["kernel_name"]),
        kernel_display_name=str(raw_environment["kernel_display_name"]),
        notebooks_dir=_resolve_project_path(str(raw_environment["notebooks_dir"]), project_root),
        notebook_docs_dir=_resolve_project_path(str(raw_environment["notebook_docs_dir"]), project_root),
    )


def _load_notebook(raw_notebook: dict[str, object], project_root: Path) -> ManagedNotebook:
    source_dataset_ids = tuple(str(item) for item in raw_notebook.get("source_dataset_ids", []))
    output_dataset_ids = tuple(str(item) for item in raw_notebook.get("output_dataset_ids", []))
    notebook_id = _ensure_slug(str(raw_notebook["notebook_id"]), "notebook_id")
    stage = _ensure_slug(str(raw_notebook["stage"]), "stage")
    topic = _ensure_slug(str(raw_notebook["topic"]), "topic")

    return ManagedNotebook(
        notebook_id=notebook_id,
        order=int(raw_notebook["order"]),
        stage=stage,
        topic=topic,
        notebook_path=_resolve_project_path(str(raw_notebook["path"]), project_root),
        doc_path=_resolve_project_path(str(raw_notebook["doc_path"]), project_root),
        template_profile=str(raw_notebook["template_profile"]),
        source_dataset_ids=source_dataset_ids,
        output_dataset_ids=output_dataset_ids,
    )


def _manifest_issues(governance: ProjectGovernance) -> list[str]:
    issues: list[str] = []

    if not governance.notebooks:
        issues.append("project_governance.toml debe registrar al menos un notebook oficial.")
        return issues

    notebook_ids = [entry.notebook_id for entry in governance.notebooks]
    orders = [entry.order for entry in governance.notebooks]
    notebook_paths = [entry.notebook_path.resolve() for entry in governance.notebooks]
    doc_paths = [entry.doc_path.resolve() for entry in governance.notebooks]

    duplicate_ids = sorted({item for item in notebook_ids if notebook_ids.count(item) > 1})
    if duplicate_ids:
        issues.append(f"Los notebooks oficiales no deben repetir notebook_id: {duplicate_ids}.")

    duplicate_orders = sorted({item for item in orders if orders.count(item) > 1})
    if duplicate_orders:
        issues.append(f"Los notebooks oficiales no deben repetir order: {duplicate_orders}.")

    duplicate_notebook_paths = sorted(
        {
            str(path.relative_to(governance.project_root))
            for path in notebook_paths
            if notebook_paths.count(path) > 1
        }
    )
    if duplicate_notebook_paths:
        issues.append(f"Los notebooks oficiales no deben repetir path: {duplicate_notebook_paths}.")

    duplicate_doc_paths = sorted(
        {
            str(path.relative_to(governance.project_root))
            for path in doc_paths
            if doc_paths.count(path) > 1
        }
    )
    if duplicate_doc_paths:
        issues.append(f"Los notebooks oficiales no deben repetir doc_path: {duplicate_doc_paths}.")

    for entry in governance.notebooks:
        expected_prefix = f"{entry.order:02d}_"
        if not entry.notebook_path.name.startswith(expected_prefix):
            issues.append(
                f"{entry.notebook_path}: el nombre del notebook debe empezar con '{expected_prefix}'."
            )
        if entry.notebook_path.parent.resolve() != governance.environment.notebooks_dir.resolve():
            issues.append(
                f"{entry.notebook_path}: todo notebook oficial debe vivir en '{governance.environment.notebooks_dir}'."
            )
        if entry.doc_path.parent.resolve() != governance.environment.notebook_docs_dir.resolve():
            issues.append(
                f"{entry.doc_path}: todo export oficial debe vivir en '{governance.environment.notebook_docs_dir}'."
            )
        if entry.template_profile != "official_v1":
            issues.append(
                f"{entry.notebook_id}: template_profile no soportado '{entry.template_profile}'."
            )
        if entry.order < 1:
            issues.append(f"{entry.notebook_id}: order debe ser >= 1.")

    return issues


def load_project_governance(
    config_path: Path | None = None,
    project_root: Path | None = None,
) -> ProjectGovernance:
    effective_project_root = (project_root or PROJECT_ROOT).resolve()
    effective_config_path = (config_path or (effective_project_root / "config" / "project_governance.toml")).resolve()
    payload = tomllib.loads(effective_config_path.read_text(encoding="utf-8"))
    environment = _load_environment(payload["environment"], effective_project_root)
    notebooks = tuple(
        sorted(
            (_load_notebook(item, effective_project_root) for item in payload.get("notebooks", [])),
            key=lambda entry: entry.order,
        )
    )
    governance = ProjectGovernance(
        project_root=effective_project_root,
        config_path=effective_config_path,
        environment=environment,
        notebooks=notebooks,
    )
    issues = _manifest_issues(governance)
    if issues:
        raise ValueError(" ".join(issues))
    return governance


def next_notebook_order(governance: ProjectGovernance) -> int:
    if not governance.notebooks:
        return 1
    return max(entry.order for entry in governance.notebooks) + 1


def _toml_value(value: object) -> str:
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, (tuple, list)):
        return "[" + ", ".join(_toml_value(item) for item in value) + "]"
    raise TypeError(f"Valor TOML no soportado: {value!r}")


def _relative_to_root(path: Path, project_root: Path) -> str:
    return path.resolve().relative_to(project_root.resolve()).as_posix()


def render_project_governance_toml(governance: ProjectGovernance) -> str:
    environment = governance.environment
    lines = [
        "[environment]",
        f"python_version = {_toml_value(environment.python_version)}",
        f"kernel_name = {_toml_value(environment.kernel_name)}",
        f"kernel_display_name = {_toml_value(environment.kernel_display_name)}",
        f"notebooks_dir = {_toml_value(_relative_to_root(environment.notebooks_dir, governance.project_root))}",
        f"notebook_docs_dir = {_toml_value(_relative_to_root(environment.notebook_docs_dir, governance.project_root))}",
        "",
    ]

    for entry in sorted(governance.notebooks, key=lambda notebook: notebook.order):
        lines.extend(
            [
                "[[notebooks]]",
                f"notebook_id = {_toml_value(entry.notebook_id)}",
                f"order = {entry.order}",
                f"stage = {_toml_value(entry.stage)}",
                f"topic = {_toml_value(entry.topic)}",
                f"path = {_toml_value(_relative_to_root(entry.notebook_path, governance.project_root))}",
                f"doc_path = {_toml_value(_relative_to_root(entry.doc_path, governance.project_root))}",
                f"template_profile = {_toml_value(entry.template_profile)}",
                f"source_dataset_ids = {_toml_value(entry.source_dataset_ids)}",
                f"output_dataset_ids = {_toml_value(entry.output_dataset_ids)}",
                "",
            ]
        )

    return "\n".join(lines).rstrip() + "\n"


def write_project_governance(governance: ProjectGovernance, config_path: Path | None = None) -> Path:
    target_path = (config_path or governance.config_path).resolve()
    target_path.write_text(render_project_governance_toml(governance), encoding="utf-8")
    return target_path
