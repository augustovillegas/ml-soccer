from pathlib import Path

import pandas as pd
import pytest

from football_ml.config import MatchHistoryConfig
from football_ml.ingest import matchhistory


class DummyLogger:
    def info(self, *args, **kwargs) -> None:
        return None

    def warning(self, *args, **kwargs) -> None:
        return None

    def error(self, *args, **kwargs) -> None:
        return None

    def exception(self, *args, **kwargs) -> None:
        return None


def _build_config(tmp_path: Path) -> MatchHistoryConfig:
    return MatchHistoryConfig(
        league="ENG-Premier League",
        seasons=("2122",),
        mode="refresh_hybrid",
        raw_dir=tmp_path / "raw",
        inbox_dir=tmp_path / "inbox",
        manifest_dir=tmp_path / "manifests",
        required_columns=("Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG", "FTR"),
    )


def _sample_matches_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "Date": "13/08/2021",
                "HomeTeam": "Brentford",
                "AwayTeam": "Arsenal",
                "FTHG": 2,
                "FTAG": 0,
                "FTR": "H",
            },
            {
                "Date": "14/08/2021",
                "HomeTeam": "Málaga",
                "AwayTeam": "Chelsea",
                "FTHG": 1,
                "FTAG": 1,
                "FTR": "D",
            },
        ]
    )


def _write_csv(path: Path, encoding: str = "utf-8-sig") -> None:
    _sample_matches_frame().to_csv(path, index=False, encoding=encoding)


def test_read_csv_with_fallback_reads_latin1_csv(tmp_path: Path) -> None:
    csv_path = tmp_path / "sample.csv"
    _write_csv(csv_path, encoding="latin-1")

    dataframe, encoding = matchhistory.read_csv_with_fallback(csv_path)

    assert encoding == "latin-1"
    assert dataframe.loc[1, "HomeTeam"] == "Málaga"


def test_write_and_load_manifest_roundtrip(tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.json"
    payload = {"season": "2122", "status": "updated_manual", "sha256": "abc123"}

    matchhistory.write_manifest(manifest_path, payload)

    assert matchhistory.load_manifest(manifest_path) == payload


def test_refresh_season_uses_manual_fallback_when_provider_is_unavailable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = _build_config(tmp_path)
    matchhistory.ensure_directories(config)
    manual_csv = config.inbox_dir / "E0_2122.csv"
    _write_csv(manual_csv)

    monkeypatch.setattr(
        matchhistory,
        "download_candidate",
        lambda *args, **kwargs: (_ for _ in ()).throw(ConnectionError("HTTP 503")),
    )
    monkeypatch.setattr(
        matchhistory,
        "_expected_provider_url",
        lambda *args, **kwargs: ("https://example.com/E0_2122.csv", "E0"),
    )

    result = matchhistory.refresh_season(config, "2122", DummyLogger(), force_write=False)

    assert result["status"] == "updated_manual"
    assert result["source_mode"] == "manual_csv"
    assert config.canonical_csv_path("2122").exists()
    assert config.manifest_path("2122").exists()


def test_refresh_season_keeps_current_when_provider_and_manual_are_unavailable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = _build_config(tmp_path)
    matchhistory.ensure_directories(config)
    canonical_csv = config.canonical_csv_path("2122")
    _write_csv(canonical_csv)

    monkeypatch.setattr(
        matchhistory,
        "download_candidate",
        lambda *args, **kwargs: (_ for _ in ()).throw(ConnectionError("HTTP 503")),
    )
    monkeypatch.setattr(
        matchhistory,
        "_expected_provider_url",
        lambda *args, **kwargs: ("https://example.com/E0_2122.csv", "E0"),
    )

    result = matchhistory.refresh_season(config, "2122", DummyLogger(), force_write=False)

    assert result["status"] == "provider_unavailable_keep_current"
    assert result["sha256"] == matchhistory.sha256_file(canonical_csv)
