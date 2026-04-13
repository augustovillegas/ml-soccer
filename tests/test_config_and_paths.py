from pathlib import Path

import pytest

from football_ml.config import load_ingestion_config
from football_ml.paths import (
    PROJECT_ROOT,
    iter_managed_datasets,
    iter_managed_notebooks,
)


def test_load_ingestion_config_resolves_project_paths() -> None:
    config = load_ingestion_config()

    assert config.league == "ENG-Premier League"
    assert config.seasons == ("2122", "2223", "2324")
    assert config.raw_dir == PROJECT_ROOT / "data" / "bronze" / "matchhistory" / "raw"
    assert config.inbox_dir == PROJECT_ROOT / "data" / "bronze" / "matchhistory" / "inbox"
    assert config.manifest_dir == PROJECT_ROOT / "data" / "bronze" / "matchhistory" / "manifests"


def test_managed_notebooks_have_registered_docs_and_ids() -> None:
    notebooks = iter_managed_notebooks()

    assert len(notebooks) == 2

    for notebook in notebooks:
        assert notebook.notebook_path.suffix == ".ipynb"
        assert notebook.doc_path.name.endswith("_cells.md")
        assert notebook.expected_cell_ids
        assert all("-" in cell_id or cell_id.isalnum() for cell_id in notebook.expected_cell_ids)


def test_managed_datasets_define_scalable_contracts() -> None:
    datasets = iter_managed_datasets()
    dataset_ids = {dataset.dataset_id for dataset in datasets}

    assert dataset_ids == {
        "matchhistory_bronze_matches",
        "matchhistory_silver_matches",
    }

    silver_dataset = next(dataset for dataset in datasets if dataset.stage == "silver")

    for dataset in datasets:
        assert dataset.stage in {"bronze", "silver", "gold"}
        assert dataset.domain == "matchhistory"
        assert dataset.required_columns
        assert dataset.unique_key
        assert dataset.update_policy

    assert silver_dataset.allow_stage_root_file is True
    assert silver_dataset.transition_note


@pytest.mark.smoke
def test_managed_datasets_exist_locally_when_project_data_is_available() -> None:
    missing_paths = [dataset.path for dataset in iter_managed_datasets() if not dataset.path.exists()]
    if missing_paths:
        pytest.skip(f"Faltan datasets locales persistidos: {missing_paths}")

    for dataset in iter_managed_datasets():
        assert dataset.path.exists()
        assert dataset.path.is_file()
