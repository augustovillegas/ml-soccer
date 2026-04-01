from __future__ import annotations

from argparse import ArgumentParser
from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import hashlib

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


def build_manual_candidate(config: MatchHistoryConfig, season: str) -> SourceCandidate:
    source_path = config.inbox_dir / config.canonical_filename(season)
    if not source_path.exists():
        raise FileNotFoundError(
            "No hay CSV manual disponible para el fallback. "
            f"Coloca '{source_path.name}' en '{config.inbox_dir}'."
        )
    return SourceCandidate(
        season=season,
        mode="manual_csv",
        source_path=source_path,
        source_file=str(relative_to_project(source_path)),
    )


def download_candidate(config: MatchHistoryConfig, season: str) -> SourceCandidate:
    reader = sd.MatchHistory(
        leagues=config.league,
        seasons=[season],
        data_dir=config.raw_dir,
    )
    league_code = reader._selected_leagues[config.league]
    source_url = PROVIDER_URL_MASK.format(season=season, league_code=league_code)
    cache_path = config.raw_dir / f"{league_code}_{season}.csv"
    reader.read_games()

    if not cache_path.exists():
        raise FileNotFoundError(f"Se esperaba el archivo descargado '{cache_path}', pero no existe.")

    return SourceCandidate(
        season=season,
        mode="soccerdata_matchhistory",
        source_path=cache_path,
        source_url=source_url,
    )


def acquire_source(config: MatchHistoryConfig, season: str, logger) -> SourceCandidate:
    try:
        logger.info("Intentando descarga automatica para la temporada %s.", season)
        return download_candidate(config, season)
    except Exception as exc:
        if not is_provider_error(exc):
            raise
        logger.warning(
            "Fallo la descarga automatica para %s (%s). Se intentara el fallback manual.",
            season,
            exc,
        )
        return build_manual_candidate(config, season)


def build_manifest(
    *,
    config: MatchHistoryConfig,
    season: str,
    source_candidate: SourceCandidate | None,
    canonical_path: Path,
    row_count: int,
    column_count: int,
    sha256: str,
    status: str,
    source_mode: str | None = None,
    source_url: str | None = None,
    source_file: str | None = None,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "league": config.league,
        "season": season,
        "source_mode": source_mode or (source_candidate.mode if source_candidate else "existing_local"),
        "saved_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "row_count": row_count,
        "column_count": column_count,
        "sha256": sha256,
        "status": status,
        "canonical_file": str(relative_to_project(canonical_path)),
    }
    resolved_source_url = source_url or (source_candidate.source_url if source_candidate else None)
    resolved_source_file = source_file or (source_candidate.source_file if source_candidate else None)
    if resolved_source_url:
        payload["source_url"] = resolved_source_url
    if resolved_source_file:
        payload["source_file"] = resolved_source_file
    return payload


def ensure_directories(config: MatchHistoryConfig) -> None:
    for path in config.iter_required_dirs():
        ensure_dir(path)


def process_existing_canonical(config: MatchHistoryConfig, season: str, logger) -> dict[str, object]:
    canonical_path = config.canonical_csv_path(season)
    manifest_path = config.manifest_path(season)
    dataframe, _ = read_csv_with_fallback(canonical_path)
    validate_required_columns(dataframe, canonical_path, config.required_columns)
    checksum = sha256_file(canonical_path)
    previous_manifest = load_manifest(manifest_path)
    payload = build_manifest(
        config=config,
        season=season,
        source_candidate=None,
        canonical_path=canonical_path,
        row_count=len(dataframe),
        column_count=len(dataframe.columns),
        sha256=checksum,
        status="skipped",
        source_mode=str(previous_manifest.get("source_mode", "existing_local")),
        source_url=previous_manifest.get("source_url"),
        source_file=previous_manifest.get("source_file"),
    )
    write_manifest(manifest_path, payload)
    logger.info("Temporada %s omitida: ya existe '%s'.", season, relative_to_project(canonical_path))
    return payload


def process_source_candidate(
    config: MatchHistoryConfig,
    season: str,
    candidate: SourceCandidate,
    logger,
) -> dict[str, object]:
    canonical_path = config.canonical_csv_path(season)
    manifest_path = config.manifest_path(season)

    dataframe, encoding = read_csv_with_fallback(candidate.source_path)
    validate_required_columns(dataframe, candidate.source_path, config.required_columns)

    source_checksum = sha256_file(candidate.source_path)
    status = "written"

    if canonical_path.exists() and sha256_file(canonical_path) == source_checksum:
        status = "skipped"
        logger.info(
            "Temporada %s omitida: '%s' no cambio respecto del archivo canonico.",
            season,
            relative_to_project(candidate.source_path),
        )
    else:
        shutil.copyfile(candidate.source_path, canonical_path)
        logger.info(
            "Temporada %s guardada desde '%s' hacia '%s' (encoding detectado: %s).",
            season,
            relative_to_project(candidate.source_path),
            relative_to_project(canonical_path),
            encoding,
        )

    checksum = sha256_file(canonical_path)
    payload = build_manifest(
        config=config,
        season=season,
        source_candidate=candidate,
        canonical_path=canonical_path,
        row_count=len(dataframe),
        column_count=len(dataframe.columns),
        sha256=checksum,
        status=status,
    )
    write_manifest(manifest_path, payload)
    return payload


def parse_args() -> ArgumentParser:
    parser = ArgumentParser(description="Ingesta bronze de MatchHistory con fallback manual.")
    parser.add_argument("--force", action="store_true", help="Reintenta la temporada aunque ya exista el CSV canonico.")
    parser.add_argument("--seasons", nargs="+", help="Lista de temporadas a procesar. Ejemplo: 2122 2223 2324.")
    return parser


def main() -> int:
    args = parse_args().parse_args()
    config = load_ingestion_config()
    seasons = tuple(str(season) for season in (args.seasons or config.seasons))
    logger, log_path = configure_logger("ingest-matchhistory")

    ensure_directories(config)
    logger.info("Iniciando ingesta MatchHistory. Log: %s", log_path)
    logger.info("Liga configurada: %s | Temporadas: %s | Modo: %s", config.league, seasons, config.mode)

    results: list[dict[str, object]] = []
    try:
        for season in seasons:
            canonical_path = config.canonical_csv_path(season)
            if canonical_path.exists() and not args.force:
                results.append(process_existing_canonical(config, season, logger))
                continue

            candidate = acquire_source(config, season, logger)
            results.append(process_source_candidate(config, season, candidate, logger))
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

