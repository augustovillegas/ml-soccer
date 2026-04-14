from __future__ import annotations

from argparse import ArgumentParser
import json
from pathlib import Path
import tomllib

from football_ml.export_notebook_cells import export_all_managed_notebooks
from football_ml.governance import ProjectGovernance, load_project_governance


def parse_args() -> ArgumentParser:
    parser = ArgumentParser(description="Sincroniza artefactos gobernados del proyecto.")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verifica si docs/notebooks/README.md y requirements.txt estan sincronizados.",
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
        doc_rel = entry.doc_path.relative_to(governance.project_root).as_posix()
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


def sync_project(
    config_path: Path | None = None,
    project_root: Path | None = None,
) -> list[Path]:
    governance = load_project_governance(config_path=config_path, project_root=project_root)
    exported_paths = export_all_managed_notebooks(managed_notebooks=governance.notebooks)
    synced_paths = list(exported_paths)
    synced_paths.append(sync_notebooks_index(governance))
    synced_paths.append(sync_requirements(governance.project_root / "pyproject.toml", governance.project_root / "requirements.txt"))
    return synced_paths


def main() -> int:
    args = parse_args().parse_args()
    governance = load_project_governance()

    if args.check:
        issues = []
        issues.extend(check_notebooks_index_sync(governance))
        issues.extend(check_requirements_sync(governance.project_root / "pyproject.toml", governance.project_root / "requirements.txt"))
        if issues:
            for issue in issues:
                print(issue)
            return 1
        print("Project governance artifacts are synchronized.")
        return 0

    synced_paths = sync_project()
    print("Project synchronized:")
    for path in synced_paths:
        print(f"- {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
