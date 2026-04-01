from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import tomllib

from football_ml.paths import CONFIG_DIR, PROJECT_ROOT


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", value.lower())
    return slug.strip("_")


@dataclass(frozen=True)
class MatchHistoryConfig:
    league: str
    seasons: tuple[str, ...]
    mode: str
    raw_dir: Path
    inbox_dir: Path
    manifest_dir: Path
    required_columns: tuple[str, ...]

    @property
    def league_slug(self) -> str:
        return _slugify(self.league)

    def canonical_filename(self, season: str) -> str:
        return f"{self.league_slug}_{season}.csv"

    def manual_fallback_filename(self, season: str) -> str:
        return f"E0_{season}.csv"

    def manual_fallback_candidates(self, season: str) -> tuple[str, ...]:
        return (self.manual_fallback_filename(season), self.canonical_filename(season))

    def canonical_csv_path(self, season: str) -> Path:
        return self.raw_dir / self.canonical_filename(season)

    def manifest_path(self, season: str) -> Path:
        return self.manifest_dir / f"{self.league_slug}_{season}.json"

    def iter_required_dirs(self) -> tuple[Path, ...]:
        return (self.raw_dir, self.inbox_dir, self.manifest_dir)


@dataclass(frozen=True)
class AutomationConfig:
    task_name: str
    schedule_time: str


def load_ingestion_config(config_path: Path | None = None) -> MatchHistoryConfig:
    config_file = config_path or (CONFIG_DIR / "ingestion.toml")
    payload = tomllib.loads(config_file.read_text(encoding="utf-8"))
    data = payload["matchhistory"]

    return MatchHistoryConfig(
        league=data["league"],
        seasons=tuple(str(season) for season in data["seasons"]),
        mode=data["mode"],
        raw_dir=_resolve_project_path(data["raw_dir"]),
        inbox_dir=_resolve_project_path(data["inbox_dir"]),
        manifest_dir=_resolve_project_path(data["manifest_dir"]),
        required_columns=tuple(data["required_columns"]),
    )


def load_automation_config(config_path: Path | None = None) -> AutomationConfig:
    config_file = config_path or (CONFIG_DIR / "ingestion.toml")
    payload = tomllib.loads(config_file.read_text(encoding="utf-8"))
    data = payload["automation"]

    return AutomationConfig(
        task_name=data["task_name"],
        schedule_time=data["schedule_time"],
    )


def _resolve_project_path(raw_path: str) -> Path:
    path = Path(raw_path)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path
