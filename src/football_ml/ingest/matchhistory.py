from __future__ import annotations

from argparse import ArgumentParser
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import hashlib
from pathlib import Path
import shutil
import tempfile

import pandas as pd
import soccerdata as sd

from football_ml.config import MatchHistoryConfig, load_ingestion_config
from football_ml.logging_utils import configure_logger
from football_ml.paths import ensure_dir, relative_to_project


PROVIDER_URL_MASK = "https://www.football-data.co.uk/mmz4281/{season}/{league_code}.csv"


@dataclass(frozen=True)
class SourceCandidate:
    season: str
    mode: str
    source_path: Path
    source_url: str | None = None
    source_file: str | None = None
    cleanup_dir: Path | None = None


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def read_csv_with_fallback(path: Path) -> tuple[pd.DataFrame, str]:
    last_error: Exception | None = None
    for encoding in ("utf-8-sig", "latin-1"):
        try:
            return pd.read_csv(path, encoding=encoding), encoding
        except UnicodeDecodeError as exc:
            last_error = exc
    raise ValueError(f"No se pudo leer '{path}' con utf-8-sig ni latin-1: {last_error}")


def validate_required_columns(df: pd.DataFrame, path: Path, required_columns: tuple[str, ...]) -> None:
    missing = [column for column in required_columns if column not in df.columns]
    if missing:
        raise ValueError(f"El archivo '{path}' no tiene las columnas minimas requeridas: {missing}")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file_handle:
        for chunk in iter(lambda: file_handle.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_manifest(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def load_manifest(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def is_provider_error(exc: Exception) -> bool:
    message = str(exc)
    exc_name = type(exc).__name__
    return (
        exc_name in {"ConnectionError", "HTTPError"}
        or "Could not download" in message
        or "football-data.co.uk" in message
        or "503" in message
    )


def infer_saved_at(previous_manifest: dict[str, object], canonical_path: Path) -> str | None:
    saved_at = previous_manifest.get("saved_at_utc")
    if isinstance(saved_at, str) and saved_at:
        return saved_at
    if canonical_path.exists():
        return datetime.fromtimestamp(canonical_path.stat().st_mtime, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return None


def build_manual_candidate(config: MatchHistoryConfig, season: str) -> SourceCandidate:
    source_path: Path | None = None
    for filename in config.manual_fallback_candidates(season):
        candidate_path = config.inbox_dir / filename
        if candidate_path.exists():
            source_path = candidate_path
            break

    if source_path is None:
        raise FileNotFoundError(
            "No hay CSV manual disponible para el fallback. "
            f"Coloca '{config.manual_fallback_filename(season)}' en '{config.inbox_dir}'."
        )
    return SourceCandidate(
        season=season,
        mode="manual_csv",
        source_path=source_path,
        source_file=str(relative_to_project(source_path)),
    )


def _expected_provider_url(config: MatchHistoryConfig, season: str, data_dir: Path) -> tuple[str, str]:
    reader = sd.MatchHistory(
        leagues=config.league,
        seasons=[season],
        data_dir=data_dir,
    )
    league_code = reader._selected_leagues[config.league]
    return PROVIDER_URL_MASK.format(season=season, league_code=league_code), league_code


def download_candidate(config: MatchHistoryConfig, season: str) -> SourceCandidate:
    temp_dir = Path(tempfile.mkdtemp(prefix="football-ml-matchhistory-"))
    try:
        source_url, league_code = _expected_provider_url(config, season, temp_dir)
        reader = sd.MatchHistory(
            leagues=config.league,
            seasons=[season],
            data_dir=temp_dir,
        )
        cache_path = temp_dir / f"{league_code}_{season}.csv"
        reader.read_games()

        if not cache_path.exists():
            raise FileNotFoundError(f"Se esperaba el archivo descargado '{cache_path}', pero no existe.")

        return SourceCandidate(
            season=season,
            mode="soccerdata_matchhistory",
            source_path=cache_path,
            source_url=source_url,
            cleanup_dir=temp_dir,
        )
    except Exception:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise


def build_manifest(
    *,
    config: MatchHistoryConfig,
    season: str,
    status: str,
    source_mode: str,
    canonical_path: Path,
    last_checked_at_utc: str,
    saved_at_utc: str | None,
    row_count: int | None,
    column_count: int | None,
    sha256: str | None,
    previous_sha256: str | None,
    source_url: str | None = None,
    source_file: str | None = None,
) -> dict[str, object]:
    return {
        "league": config.league,
        "season": season,
        "status": status,
        "source_mode": source_mode,
        "source_url": source_url,
        "source_file": source_file,
        "last_checked_at_utc": last_checked_at_utc,
        "saved_at_utc": saved_at_utc,
        "row_count": row_count,
        "column_count": column_count,
        "sha256": sha256,
        "previous_sha256": previous_sha256,
        "canonical_file": str(relative_to_project(canonical_path)),
    }


def ensure_directories(config: MatchHistoryConfig) -> None:
    for path in config.iter_required_dirs():
        ensure_dir(path)


def cleanup_candidate(candidate: SourceCandidate) -> None:
    if candidate.cleanup_dir:
        shutil.rmtree(candidate.cleanup_dir, ignore_errors=True)


def canonical_checksum(path: Path) -> str | None:
    if not path.exists():
        return None
    return sha256_file(path)


def process_source_candidate(
    config: MatchHistoryConfig,
    season: str,
    candidate: SourceCandidate,
    logger,
    previous_manifest: dict[str, object],
    force_write: bool,
) -> dict[str, object]:
    canonical_path = config.canonical_csv_path(season)
    manifest_path = config.manifest_path(season)
    checked_at = utc_now()
    current_checksum = canonical_checksum(canonical_path)

    dataframe, encoding = read_csv_with_fallback(candidate.source_path)
    validate_required_columns(dataframe, candidate.source_path, config.required_columns)

    source_checksum = sha256_file(candidate.source_path)
    if candidate.mode == "soccerdata_matchhistory":
        updated_status = "updated_remote"
        no_change_status = "no_change_remote"
    else:
        updated_status = "updated_manual"
        no_change_status = "no_change_manual"

    if canonical_path.exists() and current_checksum == source_checksum and not force_write:
        status = no_change_status
        saved_at = infer_saved_at(previous_manifest, canonical_path)
        logger.info(
            "Temporada %s sin cambios desde '%s'. Se conserva '%s'.",
            season,
            relative_to_project(candidate.source_path),
            relative_to_project(canonical_path),
        )
    else:
        shutil.copyfile(candidate.source_path, canonical_path)
        status = updated_status
        saved_at = checked_at
        logger.info(
            "Temporada %s actualizada desde '%s' hacia '%s' (encoding detectado: %s).",
            season,
            relative_to_project(candidate.source_path),
            relative_to_project(canonical_path),
            encoding,
        )

    payload = build_manifest(
        config=config,
        season=season,
        status=status,
        source_mode=candidate.mode,
        canonical_path=canonical_path,
        last_checked_at_utc=checked_at,
        saved_at_utc=saved_at,
        row_count=len(dataframe),
        column_count=len(dataframe.columns),
        sha256=source_checksum,
        previous_sha256=current_checksum,
        source_url=candidate.source_url,
        source_file=candidate.source_file,
    )
    write_manifest(manifest_path, payload)
    return payload


def process_provider_unavailable_keep_current(
    config: MatchHistoryConfig,
    season: str,
    previous_manifest: dict[str, object],
    logger,
    source_url: str,
) -> dict[str, object]:
    canonical_path = config.canonical_csv_path(season)
    manifest_path = config.manifest_path(season)
    dataframe, _ = read_csv_with_fallback(canonical_path)
    validate_required_columns(dataframe, canonical_path, config.required_columns)
    current_checksum = sha256_file(canonical_path)

    payload = build_manifest(
        config=config,
        season=season,
        status="provider_unavailable_keep_current",
        source_mode=str(previous_manifest.get("source_mode", "existing_local")),
        canonical_path=canonical_path,
        last_checked_at_utc=utc_now(),
        saved_at_utc=infer_saved_at(previous_manifest, canonical_path),
        row_count=len(dataframe),
        column_count=len(dataframe.columns),
        sha256=current_checksum,
        previous_sha256=current_checksum,
        source_url=source_url,
        source_file=previous_manifest.get("source_file"),
    )
    write_manifest(manifest_path, payload)
    logger.warning(
        "Temporada %s mantiene el CSV canonico existente por indisponibilidad temporal del proveedor.",
        season,
    )
    return payload


def process_failed_no_source(
    config: MatchHistoryConfig,
    season: str,
    previous_manifest: dict[str, object],
    logger,
    source_url: str,
) -> None:
    canonical_path = config.canonical_csv_path(season)
    manifest_path = config.manifest_path(season)
    manual_file = str(relative_to_project(config.inbox_dir / config.manual_fallback_filename(season)))
    payload = build_manifest(
        config=config,
        season=season,
        status="failed_no_source",
        source_mode="none",
        canonical_path=canonical_path,
        last_checked_at_utc=utc_now(),
        saved_at_utc=previous_manifest.get("saved_at_utc"),
        row_count=None,
        column_count=None,
        sha256=None,
        previous_sha256=previous_manifest.get("sha256"),
        source_url=source_url,
        source_file=manual_file,
    )
    write_manifest(manifest_path, payload)
    logger.error(
        "Temporada %s fallo: no hay fuente remota utilizable ni CSV manual en inbox.",
        season,
    )
    raise FileNotFoundError(
        "No hay CSV manual disponible para el fallback. "
        f"Coloca '{config.manual_fallback_filename(season)}' en '{config.inbox_dir}'."
    )


def refresh_season(
    config: MatchHistoryConfig,
    season: str,
    logger,
    force_write: bool,
) -> dict[str, object]:
    canonical_path = config.canonical_csv_path(season)
    manifest_path = config.manifest_path(season)
    previous_manifest = load_manifest(manifest_path)
    source_url, _ = _expected_provider_url(config, season, config.raw_dir)

    try:
        candidate = download_candidate(config, season)
        try:
            return process_source_candidate(config, season, candidate, logger, previous_manifest, force_write)
        finally:
            cleanup_candidate(candidate)
    except Exception as exc:
        if not is_provider_error(exc):
            raise

        logger.warning(
            "Fallo la descarga automatica para %s (%s). Se intentara el fallback manual.",
            season,
            exc,
        )

        try:
            candidate = build_manual_candidate(config, season)
            return process_source_candidate(config, season, candidate, logger, previous_manifest, force_write)
        except FileNotFoundError:
            if canonical_path.exists():
                return process_provider_unavailable_keep_current(config, season, previous_manifest, logger, source_url)
            process_failed_no_source(config, season, previous_manifest, logger, source_url)
            raise


def parse_args() -> ArgumentParser:
    parser = ArgumentParser(description="Ingesta bronze de MatchHistory con refresh y fallback manual.")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Sobrescribe el CSV canonico aunque el checksum no haya cambiado.",
    )
    parser.add_argument("--seasons", nargs="+", help="Lista de temporadas a procesar. Ejemplo: 2122 2223 2324.")
    return parser


def main() -> int:
    args = parse_args().parse_args()
    config = load_ingestion_config()
    seasons = tuple(str(season) for season in (args.seasons or config.seasons))
    logger, log_path = configure_logger("ingest-matchhistory")

    ensure_directories(config)
    logger.info("Iniciando refresh MatchHistory. Log: %s", log_path)
    logger.info("Liga configurada: %s | Temporadas: %s | Modo: %s", config.league, seasons, config.mode)

    results: list[dict[str, object]] = []
    try:
        for season in seasons:
            results.append(refresh_season(config, season, logger, args.force))
    except Exception as exc:
        logger.exception("La ingesta fallo: %s", exc)
        print(f"Ingestion failed. Revisa el log: {log_path}")
        print(str(exc))
        return 1

    print("Ingestion completed.")
    print(f"Log: {log_path}")
    for result in results:
        print(
            f"- {result['season']}: {result['status']} | {result['source_mode']} | "
            f"{result['canonical_file']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
