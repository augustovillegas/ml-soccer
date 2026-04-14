from dataclasses import dataclass
from pathlib import Path

from football_ml.governance import CONFIG_DIR, ManagedNotebook, PROJECT_ROOT, load_project_governance


DATA_DIR = PROJECT_ROOT / "data"
DOCS_DIR = PROJECT_ROOT / "docs"
LOGS_DIR = PROJECT_ROOT / "logs"
INGESTION_LOGS_DIR = LOGS_DIR / "ingestion"
MATCHHISTORY_DIR = DATA_DIR / "bronze" / "matchhistory"
MATCHHISTORY_RAW_DIR = MATCHHISTORY_DIR / "raw"
MATCHHISTORY_INBOX_DIR = MATCHHISTORY_DIR / "inbox"
MATCHHISTORY_MANIFEST_DIR = MATCHHISTORY_DIR / "manifests"
MATCHHISTORY_SILVER_DIR = DATA_DIR / "silver" / "matchhistory"
MATCHHISTORY_BRONZE_PARQUET_PATH = MATCHHISTORY_RAW_DIR / "matches_bronze.parquet"
MATCHHISTORY_SILVER_PARQUET_PATH = DATA_DIR / "silver" / "matches_silver.parquet"
PROJECT_GOVERNANCE = load_project_governance()
GOVERNED_ENVIRONMENT = PROJECT_GOVERNANCE.environment
NOTEBOOKS_DIR = GOVERNED_ENVIRONMENT.notebooks_dir
NOTEBOOK_DOCS_DIR = GOVERNED_ENVIRONMENT.notebook_docs_dir
EXPECTED_PYTHON_VERSION = GOVERNED_ENVIRONMENT.python_version
EXPECTED_PYTHON = PROJECT_ROOT / ".venv" / "Scripts" / "python.exe"
EXPECTED_KERNEL_NAME = GOVERNED_ENVIRONMENT.kernel_name
EXPECTED_KERNEL_DISPLAY_NAME = GOVERNED_ENVIRONMENT.kernel_display_name


@dataclass(frozen=True)
class ManagedDataset:
    dataset_id: str
    stage: str
    domain: str
    path: Path
    required_columns: tuple[str, ...]
    unique_key: tuple[str, ...]
    update_policy: str
    allow_stage_root_file: bool = False
    transition_note: str | None = None


MANAGED_NOTEBOOKS = PROJECT_GOVERNANCE.notebooks

MANAGED_DATASETS = (
    ManagedDataset(
        dataset_id="matchhistory_bronze_matches",
        stage="bronze",
        domain="matchhistory",
        path=MATCHHISTORY_BRONZE_PARQUET_PATH,
        required_columns=(
            "Date",
            "HomeTeam",
            "AwayTeam",
            "season",
            "league",
            "FTR",
            "FTHG",
            "FTAG",
        ),
        unique_key=("Date", "HomeTeam", "AwayTeam", "season"),
        update_policy="exploratory_notebook_owner_until_script_promotion",
    ),
    ManagedDataset(
        dataset_id="matchhistory_silver_matches",
        stage="silver",
        domain="matchhistory",
        path=MATCHHISTORY_SILVER_PARQUET_PATH,
        required_columns=(
            "game_key",
            "Date",
            "season",
            "league",
            "HomeTeam",
            "AwayTeam",
            "FTR",
            "target",
        ),
        unique_key=("game_key",),
        update_policy="exploratory_notebook_owner_until_second_consumer",
        allow_stage_root_file=True,
        transition_note="Excepcion transitoria: matches_silver.parquet permanece en data/silver hasta que exista un segundo dataset silver oficial.",
    ),
)

NOTEBOOK_PATH = MANAGED_NOTEBOOKS[0].notebook_path
NOTEBOOK_CELLS_DOC_PATH = MANAGED_NOTEBOOKS[0].doc_path


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def iter_managed_notebooks() -> tuple[ManagedNotebook, ...]:
    return MANAGED_NOTEBOOKS


def managed_notebook_paths() -> tuple[Path, ...]:
    return tuple(entry.notebook_path for entry in MANAGED_NOTEBOOKS)


def managed_notebook_doc_paths() -> tuple[Path, ...]:
    return tuple(entry.doc_path for entry in MANAGED_NOTEBOOKS)


def iter_managed_datasets() -> tuple[ManagedDataset, ...]:
    return MANAGED_DATASETS


def relative_to_project(path: Path) -> Path:
    try:
        return path.resolve().relative_to(PROJECT_ROOT.resolve())
    except ValueError:
        return path.resolve()
