from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = PROJECT_ROOT / "config"
DATA_DIR = PROJECT_ROOT / "data"
DOCS_DIR = PROJECT_ROOT / "docs"
NOTEBOOK_DOCS_DIR = DOCS_DIR / "notebooks"
LOGS_DIR = PROJECT_ROOT / "logs"
INGESTION_LOGS_DIR = LOGS_DIR / "ingestion"
MATCHHISTORY_DIR = DATA_DIR / "bronze" / "matchhistory"
MATCHHISTORY_RAW_DIR = MATCHHISTORY_DIR / "raw"
MATCHHISTORY_INBOX_DIR = MATCHHISTORY_DIR / "inbox"
MATCHHISTORY_MANIFEST_DIR = MATCHHISTORY_DIR / "manifests"
EXPECTED_PYTHON = PROJECT_ROOT / ".venv" / "Scripts" / "python.exe"
EXPECTED_KERNEL_NAME = "football-ml"
EXPECTED_KERNEL_DISPLAY_NAME = "football-ml (.venv)"


@dataclass(frozen=True)
class ManagedNotebook:
    notebook_path: Path
    doc_path: Path


MANAGED_NOTEBOOKS = (
    ManagedNotebook(
        notebook_path=PROJECT_ROOT / "notebooks" / "01_explorer_matchhistory.ipynb",
        doc_path=NOTEBOOK_DOCS_DIR / "01_explorer_matchhistory_cells.md",
    ),
    ManagedNotebook(
        notebook_path=PROJECT_ROOT / "notebooks" / "02_silver_matchhistory.ipynb",
        doc_path=NOTEBOOK_DOCS_DIR / "02_silver_matchhistory_cells.md",
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


def relative_to_project(path: Path) -> Path:
    try:
        return path.resolve().relative_to(PROJECT_ROOT.resolve())
    except ValueError:
        return path.resolve()
