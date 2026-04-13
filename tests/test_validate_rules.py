import json
from pathlib import Path

import pandas as pd
import pytest

from football_ml.export_notebook_cells import check_generated_markdown_sync, render_markdown
from football_ml.paths import ManagedDataset, iter_managed_datasets
import football_ml.validate as validate_module
from football_ml.validate import (
    _tracked_generated_artifact_issues,
    _validate_managed_dataset,
)


def _notebook_payload(source_lines: list[str]) -> dict[str, object]:
    return {
        "cells": [
            {
                "cell_type": "code",
                "id": "imports-and-kernel-check",
                "metadata": {},
                "execution_count": None,
                "outputs": [],
                "source": source_lines,
            }
        ],
        "metadata": {},
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def test_check_generated_markdown_sync_detects_stale_markdown(tmp_path: Path) -> None:
    notebook_path = tmp_path / "01_demo.ipynb"
    output_path = tmp_path / "01_demo_cells.md"

    payload = _notebook_payload(
        [
            "# ==============================\n",
            "# 1. Demo\n",
            "# ==============================\n",
            "print('v1')\n",
        ]
    )
    notebook_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    output_path.write_text(render_markdown(notebook_path, payload), encoding="utf-8")

    payload["cells"][0]["source"] = [
        "# ==============================\n",
        "# 1. Demo\n",
        "# ==============================\n",
        "print('v2')\n",
    ]
    notebook_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    issues = check_generated_markdown_sync(notebook_path, output_path)

    assert issues
    assert "desactualizado" in issues[0]


def test_tracked_generated_artifact_issues_detect_forbidden_paths() -> None:
    issues = _tracked_generated_artifact_issues(
        [
            "notebooks/.ipynb_checkpoints/01_explorer_matchhistory-checkpoint.ipynb",
            "src/football_ml.egg-info/PKG-INFO",
            "data/silver/matches_silver.parquet",
            "logs/ingestion/run.log",
            "data/silver/.gitkeep",
        ]
    )

    assert any("checkpoints de notebook" in issue for issue in issues)
    assert any(".egg-info" in issue for issue in issues)
    assert any("artefactos de data" in issue for issue in issues)
    assert any("artefactos de logs" in issue for issue in issues)
    assert all(not issue.startswith("data/silver/.gitkeep") for issue in issues)


def test_validate_managed_dataset_rejects_new_silver_stage_root_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dataset_root = tmp_path / "data"
    dataset_path = dataset_root / "silver" / "future_matches.parquet"
    dataset_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        [{"game_key": "2021-08-13 Brentford-Arsenal", "Date": "2021-08-13", "FTR": "H"}]
    ).to_parquet(dataset_path, index=False)
    monkeypatch.setattr(validate_module, "DATA_DIR", dataset_root)

    dataset = ManagedDataset(
        dataset_id="future_silver_matches",
        stage="silver",
        domain="matchhistory",
        path=dataset_path,
        required_columns=("game_key", "Date", "FTR"),
        unique_key=("game_key",),
        update_policy="future_script_owner",
        allow_stage_root_file=False,
    )

    issues = _validate_managed_dataset(dataset)

    assert any("no deben vivir en la raiz" in issue for issue in issues)


@pytest.mark.smoke
def test_registered_datasets_pass_contract_validation_when_local_files_exist() -> None:
    missing_paths = [dataset.path for dataset in iter_managed_datasets() if not dataset.path.exists()]
    if missing_paths:
        pytest.skip(f"Faltan datasets locales persistidos: {missing_paths}")

    issues: list[str] = []
    for dataset in iter_managed_datasets():
        issues.extend(_validate_managed_dataset(dataset))

    assert not issues
