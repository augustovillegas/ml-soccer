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
NOTEBOOK_PATH = PROJECT_ROOT / "notebooks" / "01_explorer_matchhistory.ipynb"
NOTEBOOK_CELLS_DOC_PATH = NOTEBOOK_DOCS_DIR / "01_explorer_matchhistory_cells.md"
EXPECTED_PYTHON = PROJECT_ROOT / ".venv" / "Scripts" / "python.exe"
EXPECTED_KERNEL_NAME = "football-ml"
EXPECTED_KERNEL_DISPLAY_NAME = "football-ml (.venv)"


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def relative_to_project(path: Path) -> Path:
    try:
        return path.resolve().relative_to(PROJECT_ROOT.resolve())
    except ValueError:
        return path.resolve()
