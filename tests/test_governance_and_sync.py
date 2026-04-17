import json
from pathlib import Path
import textwrap

import pytest

from football_ml.governance import load_project_governance
from football_ml.governed_docs import check_generated_docs_sync, generated_doc_ids_for_changed_paths, render_bitacora
from football_ml.scaffold_notebook import scaffold_notebook
from football_ml.sync_project import check_notebooks_index_sync, check_requirements_sync, render_notebooks_index


def _write_notebook(path: Path) -> None:
    payload = {
        "cells": [
            {
                "cell_type": "code",
                "execution_count": None,
                "id": "imports-and-kernel-check",
                "metadata": {},
                "outputs": [],
                "source": [
                    "# ==============================\n",
                    "# 1. Demo\n",
                    "# ==============================\n",
                    "print('ok')\n",
                ],
            }
        ],
        "metadata": {
            "kernelspec": {
                "display_name": "football-ml (.venv)",
                "language": "python",
                "name": "football-ml",
            }
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_temp_project_governance(project_root: Path, duplicate_notebook_id: bool = False) -> Path:
    config_dir = project_root / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_path = config_dir / "project_governance.toml"
    second_notebook_id = "explorer_matchhistory" if duplicate_notebook_id else "silver_matchhistory"
    config_path.write_text(
        textwrap.dedent(
            f"""
            [environment]
            python_version = "3.13"
            kernel_name = "football-ml"
            kernel_display_name = "football-ml (.venv)"
            notebooks_dir = "notebooks"
            notebook_docs_dir = "docs/notebooks"

            [[notebooks]]
            notebook_id = "explorer_matchhistory"
            order = 1
            stage = "explorer"
            topic = "matchhistory"
            path = "notebooks/01_explorer_matchhistory.ipynb"
            doc_path = "docs/notebooks/01_explorer_matchhistory_cells.md"
            template_profile = "official_v1"
            source_dataset_ids = []
            output_dataset_ids = ["matchhistory_bronze_matches"]

            [[notebooks]]
            notebook_id = "{second_notebook_id}"
            order = 2
            stage = "silver"
            topic = "matchhistory"
            path = "notebooks/02_silver_matchhistory.ipynb"
            doc_path = "docs/notebooks/02_silver_matchhistory_cells.md"
            template_profile = "official_v1"
            source_dataset_ids = ["matchhistory_bronze_matches"]
            output_dataset_ids = ["matchhistory_silver_matches"]
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    return config_path


def test_load_project_governance_rejects_duplicate_notebook_id(tmp_path: Path) -> None:
    config_path = _write_temp_project_governance(tmp_path, duplicate_notebook_id=True)

    with pytest.raises(ValueError):
        load_project_governance(config_path=config_path, project_root=tmp_path)


def test_notebooks_index_and_requirements_are_synchronized_in_repo() -> None:
    governance = load_project_governance()

    assert not check_notebooks_index_sync(governance)
    assert not check_requirements_sync(governance.project_root / "pyproject.toml", governance.project_root / "requirements.txt")
    assert not check_generated_docs_sync(governance)


def test_scaffold_notebook_creates_next_registered_notebook(tmp_path: Path) -> None:
    config_path = _write_temp_project_governance(tmp_path)
    _write_notebook(tmp_path / "notebooks" / "01_explorer_matchhistory.ipynb")
    _write_notebook(tmp_path / "notebooks" / "02_silver_matchhistory.ipynb")
    (tmp_path / "docs" / "notebooks").mkdir(parents=True, exist_ok=True)
    (tmp_path / "pyproject.toml").write_text(
        textwrap.dedent(
            """
            [project]
            dependencies = [
              "pandas==2.3.3",
              "pytest==8.3.5",
            ]
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    (tmp_path / "requirements.txt").write_text("", encoding="utf-8")

    notebook_path, doc_path, governance_path = scaffold_notebook(
        stage="gold",
        topic="feature_lab",
        source_dataset_ids=("matchhistory_silver_matches",),
        output_dataset_ids=("matchhistory_gold_features",),
        config_path=config_path,
        project_root=tmp_path,
    )

    reloaded_governance = load_project_governance(config_path=governance_path, project_root=tmp_path)

    assert notebook_path.name == "03_gold_feature_lab.ipynb"
    assert doc_path.name == "03_gold_feature_lab_cells.md"
    assert notebook_path.exists()
    assert doc_path.exists()
    assert [entry.order for entry in reloaded_governance.notebooks] == [1, 2, 3]
    assert reloaded_governance.notebooks[-1].notebook_id == "gold_feature_lab"
    assert (tmp_path / "docs" / "notebooks" / "README.md").read_text(encoding="utf-8") == render_notebooks_index(reloaded_governance)


def test_bootstrap_script_supports_skip_scheduled_task() -> None:
    script_text = (Path(__file__).resolve().parents[1] / "scripts" / "bootstrap.ps1").read_text(encoding="utf-8")

    assert "[switch]$SkipScheduledTask" in script_text
    assert "if ($SkipScheduledTask)" in script_text
    assert "schtasks.exe /Create" in script_text
    assert "core.hooksPath .githooks" in script_text


def test_project_governance_workflow_syncs_before_validate() -> None:
    workflow_text = (
        Path(__file__).resolve().parents[1] / ".github" / "workflows" / "project-governance.yml"
    ).read_text(encoding="utf-8")

    sync_step = "run: .\\scripts\\sync-project.ps1"
    validate_step = "run: .\\scripts\\validate-project.ps1 -Scope project"

    assert sync_step in workflow_text
    assert validate_step in workflow_text
    assert workflow_text.index(sync_step) < workflow_text.index(validate_step)


def test_pre_commit_hook_passes_changed_paths_as_array() -> None:
    hook_text = (Path(__file__).resolve().parents[1] / ".githooks" / "pre-commit.ps1").read_text(encoding="utf-8")

    assert "& $syncScript -ChangedPath $changedPaths" in hook_text
    assert '@("-ChangedPath", $changedPath.Trim())' not in hook_text


def test_generated_doc_ids_for_changed_paths_match_operational_sources() -> None:
    governance = load_project_governance()

    doc_ids = generated_doc_ids_for_changed_paths({"data/bronze/matchhistory/manifests"}, governance)

    assert "project_status_doc" in doc_ids


def test_render_bitacora_is_deterministic_and_references_ledger() -> None:
    governance = load_project_governance()

    rendered = render_bitacora(governance)

    assert "### 3. `sync_project`" in rendered
    assert "> Archivo generado automaticamente desde `config/project_governance.toml`." in rendered
    assert (
        "Evidencia auditada: consultar `logs/governance/command-ledger.jsonl` para `sync_project`."
        in rendered
    )
    assert "Evidencia local de una ejecucion satisfactoria:" not in rendered
