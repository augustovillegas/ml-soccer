from __future__ import annotations

from argparse import ArgumentParser
from fnmatch import fnmatch
from pathlib import Path
import tomllib

from football_ml.export_notebook_cells import (
    check_generated_markdown_sync,
    export_all_managed_notebooks,
    export_notebook_cells,
)
from football_ml.governance import ProjectGovernance, load_project_governance
from football_ml.governed_docs import (
    check_generated_docs_sync,
    generated_doc_ids_for_changed_paths,
    sync_generated_docs,
)


SYNC_ACTIONS = {
    "generated_docs",
    "notebook_exports_all",
    "notebook_exports_changed",
    "notebooks_index",
    "requirements",
}


def parse_args() -> ArgumentParser:
    parser = ArgumentParser(description="Sincroniza artefactos gobernados del proyecto.")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verifica si artefactos generados y dependencias estan sincronizados.",
    )
    parser.add_argument(
        "--changed-path",
        action="append",
        default=[],
        help="Path relativo o absoluto que disparo la resincronizacion dirigida.",
    )
    return parser


def _requirements_dependencies_from_pyproject(pyproject_path: Path) -> tuple[str, ...]:
    payload = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    project = payload.get("project", {})
    dependencies = project.get("dependencies", [])
    if not isinstance(dependencies, list):
        raise ValueError(f"{pyproject_path}: 'project.dependencies' debe ser una lista.")
    return tuple(str(item).strip() for item in dependencies if str(item).strip())


def render_requirements_txt(pyproject_path: Path) -> str:
    dependencies = _requirements_dependencies_from_pyproject(pyproject_path)
    return "\n".join(dependencies).rstrip() + "\n"


def check_requirements_sync(pyproject_path: Path, requirements_path: Path) -> list[str]:
    expected = render_requirements_txt(pyproject_path)
    if not requirements_path.exists():
        return [f"Falta requirements.txt sincronizado: {requirements_path}"]

    actual = requirements_path.read_text(encoding="utf-8")
    if actual != expected:
        return [f"{requirements_path}: requirements.txt esta desalineado respecto de pyproject.toml."]
    return []


def sync_requirements(pyproject_path: Path, requirements_path: Path) -> Path:
    requirements_path.write_text(render_requirements_txt(pyproject_path), encoding="utf-8")
    return requirements_path


def render_notebooks_index(governance: ProjectGovernance) -> str:
    lines = [
        "# Inventario de Notebooks Oficiales",
        "",
        "> Archivo generado automaticamente desde `config/project_governance.toml`.",
        "> Regenerar con `.\\scripts\\sync-project.ps1` cuando cambie el manifiesto o un notebook oficial.",
        "",
    ]

    for entry in governance.notebooks:
        source_datasets = ", ".join(entry.source_dataset_ids) if entry.source_dataset_ids else "(ninguno)"
        output_datasets = ", ".join(entry.output_dataset_ids) if entry.output_dataset_ids else "(ninguno)"
        notebook_rel = entry.notebook_path.relative_to(governance.project_root).as_posix()
        lines.extend(
            [
                f"## {entry.order:02d} - {entry.stage} / {entry.topic}",
                "",
                f"- Notebook ID: `{entry.notebook_id}`",
                f"- Notebook: [{entry.notebook_path.name}](../../{notebook_rel})",
                f"- Export Markdown: [{entry.doc_path.name}](./{entry.doc_path.name})",
                f"- Stage: `{entry.stage}`",
                f"- Topic: `{entry.topic}`",
                f"- Template profile: `{entry.template_profile}`",
                f"- Source dataset ids: `{source_datasets}`",
                f"- Output dataset ids: `{output_datasets}`",
                "",
            ]
        )

    return "\n".join(lines).rstrip() + "\n"


def notebooks_index_path(governance: ProjectGovernance) -> Path:
    return governance.environment.notebook_docs_dir / "README.md"


def check_notebooks_index_sync(governance: ProjectGovernance) -> list[str]:
    index_path = notebooks_index_path(governance)
    expected = render_notebooks_index(governance)
    if not index_path.exists():
        return [f"Falta el inventario generado de notebooks oficiales: {index_path}"]

    actual = index_path.read_text(encoding="utf-8")
    if actual != expected:
        return [f"{index_path}: el inventario de notebooks oficiales esta desactualizado."]
    return []


def sync_notebooks_index(governance: ProjectGovernance) -> Path:
    index_path = notebooks_index_path(governance)
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(render_notebooks_index(governance), encoding="utf-8")
    return index_path


def _normalize_changed_paths(changed_paths: list[str], governance: ProjectGovernance) -> set[str]:
    normalized_paths: set[str] = set()

    for raw_path in changed_paths:
        path_text = str(raw_path).strip()
        if not path_text:
            continue
        candidate = Path(path_text)
        absolute = candidate if candidate.is_absolute() else governance.project_root / candidate
        normalized_paths.add(absolute.resolve().relative_to(governance.project_root.resolve()).as_posix())

    return normalized_paths


def _matched_watcher_actions(governance: ProjectGovernance, changed_paths: set[str]) -> set[str]:
    actions: set[str] = set()

    for rule in governance.watcher.rules:
        if any(fnmatch(changed_path, pattern) for changed_path in changed_paths for pattern in rule.patterns):
            actions.update(action for action in rule.actions if action in SYNC_ACTIONS)

    return actions


def _changed_notebook_entries(governance: ProjectGovernance, changed_paths: set[str]):
    changed_entries = []
    for entry in governance.notebooks:
        notebook_relative = entry.notebook_path.relative_to(governance.project_root).as_posix()
        if notebook_relative in changed_paths:
            changed_entries.append(entry)
    return changed_entries


def sync_project(
    config_path: Path | None = None,
    project_root: Path | None = None,
    changed_paths: list[str] | None = None,
) -> list[Path]:
    governance = load_project_governance(config_path=config_path, project_root=project_root)
    effective_changed_paths = _normalize_changed_paths(changed_paths or [], governance)
    synced_paths: list[Path] = []

    if not effective_changed_paths:
        synced_paths.extend(export_all_managed_notebooks(managed_notebooks=governance.notebooks))
        synced_paths.append(sync_notebooks_index(governance))
        synced_paths.append(
            sync_requirements(governance.project_root / "pyproject.toml", governance.project_root / "requirements.txt")
        )
        synced_paths.extend(sync_generated_docs(governance=governance))
        return synced_paths

    actions = _matched_watcher_actions(governance, effective_changed_paths)

    if "notebook_exports_all" in actions:
        synced_paths.extend(export_all_managed_notebooks(managed_notebooks=governance.notebooks))
    elif "notebook_exports_changed" in actions:
        for entry in _changed_notebook_entries(governance, effective_changed_paths):
            synced_paths.append(export_notebook_cells(entry.notebook_path, entry.doc_path))

    if "notebooks_index" in actions:
        synced_paths.append(sync_notebooks_index(governance))

    if "requirements" in actions:
        synced_paths.append(
            sync_requirements(governance.project_root / "pyproject.toml", governance.project_root / "requirements.txt")
        )

    if "generated_docs" in actions:
        synced_paths.extend(
            sync_generated_docs(
                governance=governance,
                doc_ids=generated_doc_ids_for_changed_paths(effective_changed_paths, governance),
            )
        )

    deduped_paths: list[Path] = []
    seen: set[Path] = set()
    for path in synced_paths:
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        deduped_paths.append(path)
    return deduped_paths


def check_sync(governance: ProjectGovernance) -> list[str]:
    issues: list[str] = []
    for entry in governance.notebooks:
        issues.extend(check_generated_markdown_sync(entry.notebook_path, entry.doc_path))
    issues.extend(check_notebooks_index_sync(governance))
    issues.extend(
        check_requirements_sync(governance.project_root / "pyproject.toml", governance.project_root / "requirements.txt")
    )
    issues.extend(check_generated_docs_sync(governance))
    return issues


def main() -> int:
    args = parse_args().parse_args()
    governance = load_project_governance()

    if args.check:
        issues = check_sync(governance)
        if issues:
            for issue in issues:
                print(issue)
            return 1
        print("Project governance artifacts are synchronized.")
        return 0

    synced_paths = sync_project(changed_paths=args.changed_path)
    if not synced_paths:
        print("Project synchronized with no artifact changes required.")
        return 0

    print("Project synchronized:")
    for path in synced_paths:
        print(f"- {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
