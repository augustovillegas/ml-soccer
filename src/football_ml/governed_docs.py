from __future__ import annotations

from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path

import pandas as pd

from football_ml.config import load_automation_config, load_ingestion_config
from football_ml.governance import GeneratedDoc, ProjectGovernance, load_project_governance
from football_ml.paths import iter_managed_datasets, relative_to_project


GENERATED_DOC_RENDERERS = {
    "render_bitacora",
    "render_generated_docs_index",
    "render_official_commands_doc",
    "render_project_status_doc",
}


@dataclass(frozen=True)
class DatasetSnapshot:
    dataset_id: str
    path: str
    exists: bool
    rows: int | None
    columns: int | None


def _doc_header_line(path: Path, source: str) -> list[str]:
    return [
        f"> Archivo generado automaticamente desde `{source}`.",
        "",
    ]


def _canonical_script_invocation(script_path: Path, project_root: Path) -> str:
    relative_path = script_path.resolve().relative_to(project_root.resolve()).as_posix().replace("/", "\\")
    return f".\\{relative_path}"


def _dataset_snapshot() -> tuple[DatasetSnapshot, ...]:
    snapshots: list[DatasetSnapshot] = []

    for dataset in iter_managed_datasets():
        if not dataset.path.exists():
            snapshots.append(
                DatasetSnapshot(
                    dataset_id=dataset.dataset_id,
                    path=relative_to_project(dataset.path).as_posix(),
                    exists=False,
                    rows=None,
                    columns=None,
                )
            )
            continue

        if dataset.path.suffix.lower() == ".parquet":
            dataframe = pd.read_parquet(dataset.path)
        elif dataset.path.suffix.lower() == ".csv":
            dataframe = pd.read_csv(dataset.path)
        else:
            dataframe = pd.DataFrame()

        snapshots.append(
            DatasetSnapshot(
                dataset_id=dataset.dataset_id,
                path=relative_to_project(dataset.path).as_posix(),
                exists=True,
                rows=len(dataframe),
                columns=len(dataframe.columns),
            )
        )

    return tuple(snapshots)


def _matchhistory_manifest_rows() -> list[str]:
    config = load_ingestion_config()
    lines: list[str] = []

    for season in config.seasons:
        manifest_path = config.manifest_path(season)
        if not manifest_path.exists():
            lines.append(f"- `{season}`: falta manifest oficial en `{relative_to_project(manifest_path).as_posix()}`.")
            continue

        payload = pd.read_json(manifest_path, typ="series")
        status = str(payload.get("status", "(sin estado)"))
        source_mode = str(payload.get("source_mode", "(sin source_mode)"))
        row_count = payload.get("row_count")
        column_count = payload.get("column_count")
        lines.append(
            "- "
            f"`{season}`: status=`{status}` | source_mode=`{source_mode}` | "
            f"row_count=`{row_count}` | column_count=`{column_count}`"
        )

    return lines


def render_bitacora(governance: ProjectGovernance) -> str:
    lines = [
        "# Bitacora de entorno y comandos",
        "",
        * _doc_header_line(
            governance.project_root / "BITACORA_ENTORNO.md",
            "config/project_governance.toml",
        ),
        "## Criterio operativo",
        "",
        "- La receta oficial del proyecto vive en `config/project_governance.toml`.",
        "- Esta bitacora lista solo comandos oficiales gobernados por scripts del repositorio.",
        "- Las ejecuciones reales se registran en `logs/governance/command-ledger.jsonl`.",
        "- Los comandos directos fuera de los scripts oficiales no forman parte de esta bitacora automatica.",
        "",
        "## Receta oficial",
        "",
    ]

    for command in governance.official_commands:
        lines.extend(
            [
                f"### {command.order}. `{command.command_id}`",
                "",
                "Comando base:",
                "",
                "```powershell",
                _canonical_script_invocation(command.script_path, governance.project_root),
                "```",
                "",
                f"Objetivo: {command.purpose}",
                "",
                "Verificacion minima:",
                "",
                f"- {command.verification}",
                "",
                "Artefactos impactados:",
                "",
            ]
        )
        if command.impacted_artifacts:
            lines.extend(f"- `{artifact}`" for artifact in command.impacted_artifacts)
        else:
            lines.append("- `(sin artefactos versionados declarados)`")
        lines.extend(
            [
                "",
                f"Evidencia auditada: consultar `logs/governance/command-ledger.jsonl` para `{command.command_id}`.",
                "",
            ]
        )

    return "\n".join(lines).rstrip() + "\n"


def render_official_commands_doc(governance: ProjectGovernance) -> str:
    lines = [
        "# Comandos Oficiales",
        "",
        * _doc_header_line(
            governance.project_root / "docs" / "generated" / "official-commands.md",
            "config/project_governance.toml",
        ),
        "## Registro",
        "",
    ]

    for command in governance.official_commands:
        lines.extend(
            [
                f"## {command.order:02d} - `{command.command_id}`",
                "",
                f"- Script: `{relative_to_project(command.script_path).as_posix()}`",
                f"- Comando base: `{_canonical_script_invocation(command.script_path, governance.project_root)}`",
                f"- Objetivo: {command.purpose}",
                f"- Verificacion minima: {command.verification}",
                f"- Visible en bitacora: `{str(command.document_in_bitacora).lower()}`",
                "",
            ]
        )
        if command.impacted_artifacts:
            lines.extend(f"- Artefacto impactado: `{artifact}`" for artifact in command.impacted_artifacts)
            lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def render_project_status_doc(governance: ProjectGovernance) -> str:
    automation = load_automation_config()
    ingestion = load_ingestion_config()
    dataset_snapshots = _dataset_snapshot()
    lines = [
        "# Estado Operativo Generado",
        "",
        * _doc_header_line(
            governance.project_root / "docs" / "generated" / "project-status.md",
            "config/project_governance.toml + config/ingestion.toml + datasets/manifests locales",
        ),
        "## Resumen",
        "",
        f"- Python gobernado: `{governance.environment.python_version}`",
        f"- Kernel oficial: `{governance.environment.kernel_display_name}`",
        f"- Watcher debounce: `{governance.watcher.debounce_seconds}` segundos",
        f"- Tarea oficial MatchHistory: `{automation.task_name}` a las `{automation.schedule_time}`",
        f"- Temporadas gobernadas MatchHistory: `{', '.join(ingestion.seasons)}`",
        "",
        "## Notebooks oficiales",
        "",
    ]

    for notebook in governance.notebooks:
        lines.append(
            "- "
            f"`{notebook.notebook_id}` -> `{relative_to_project(notebook.notebook_path).as_posix()}` | "
            f"doc=`{relative_to_project(notebook.doc_path).as_posix()}` | "
            f"outputs=`{', '.join(notebook.output_dataset_ids) or '(ninguno)'}`"
        )

    lines.extend(["", "## Datasets oficiales locales", ""])
    for snapshot in dataset_snapshots:
        if snapshot.exists:
            lines.append(
                "- "
                f"`{snapshot.dataset_id}` -> `{snapshot.path}` | rows=`{snapshot.rows}` | columns=`{snapshot.columns}`"
            )
        else:
            lines.append(f"- `{snapshot.dataset_id}` -> `{snapshot.path}` | pendiente localmente")

    lines.extend(["", "## Estado MatchHistory por temporada", ""])
    lines.extend(_matchhistory_manifest_rows())
    return "\n".join(lines).rstrip() + "\n"


def render_generated_docs_index(governance: ProjectGovernance) -> str:
    lines = [
        "# Documentos Generados",
        "",
        * _doc_header_line(
            governance.project_root / "docs" / "generated" / "README.md",
            "config/project_governance.toml",
        ),
        "## Inventario",
        "",
    ]

    for generated_doc in governance.generated_docs:
        lines.extend(
            [
                f"## `{generated_doc.doc_id}`",
                "",
                f"- Path: `{relative_to_project(generated_doc.path).as_posix()}`",
                f"- Generator: `{generated_doc.generator}`",
                f"- Doc class: `{generated_doc.doc_class}`",
                f"- Sources: `{', '.join(generated_doc.source_paths) or '(ninguna)'}`",
                "",
            ]
        )

    return "\n".join(lines).rstrip() + "\n"


def render_generated_doc(governance: ProjectGovernance, generated_doc: GeneratedDoc) -> str:
    if generated_doc.generator == "render_bitacora":
        return render_bitacora(governance)
    if generated_doc.generator == "render_generated_docs_index":
        return render_generated_docs_index(governance)
    if generated_doc.generator == "render_official_commands_doc":
        return render_official_commands_doc(governance)
    if generated_doc.generator == "render_project_status_doc":
        return render_project_status_doc(governance)
    raise ValueError(f"Generator no soportado: {generated_doc.generator}")


def sync_generated_docs(
    governance: ProjectGovernance | None = None,
    doc_ids: set[str] | None = None,
) -> list[Path]:
    effective_governance = governance or load_project_governance()
    synced_paths: list[Path] = []

    for generated_doc in effective_governance.generated_docs:
        if doc_ids is not None and generated_doc.doc_id not in doc_ids:
            continue
        generated_doc.path.parent.mkdir(parents=True, exist_ok=True)
        generated_doc.path.write_text(
            render_generated_doc(effective_governance, generated_doc),
            encoding="utf-8",
        )
        synced_paths.append(generated_doc.path)

    return synced_paths


def check_generated_docs_sync(governance: ProjectGovernance | None = None) -> list[str]:
    effective_governance = governance or load_project_governance()
    issues: list[str] = []

    for generated_doc in effective_governance.generated_docs:
        if not generated_doc.path.exists():
            issues.append(f"Falta el documento generado oficial: {generated_doc.path}")
            continue
        expected = render_generated_doc(effective_governance, generated_doc)
        actual = generated_doc.path.read_text(encoding="utf-8")
        if actual != expected:
            issues.append(
                f"{generated_doc.path}: el documento generado '{generated_doc.doc_id}' esta desactualizado."
            )

    return issues


def generated_doc_ids_for_changed_paths(
    changed_paths: set[str],
    governance: ProjectGovernance | None = None,
) -> set[str]:
    effective_governance = governance or load_project_governance()
    if not changed_paths:
        return {generated_doc.doc_id for generated_doc in effective_governance.generated_docs}

    doc_ids: set[str] = set()
    for generated_doc in effective_governance.generated_docs:
        if any(
            fnmatch(changed_path, source_path) or changed_path == source_path
            for source_path in generated_doc.source_paths
            for changed_path in changed_paths
        ):
            doc_ids.add(generated_doc.doc_id)

    if "logs/governance/command-ledger.jsonl" in changed_paths:
        for generated_doc in effective_governance.generated_docs:
            if generated_doc.doc_class == "ledger":
                doc_ids.add(generated_doc.doc_id)

    return doc_ids
