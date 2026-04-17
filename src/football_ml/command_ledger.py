from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

from football_ml.paths import COMMAND_LEDGER_PATH


@dataclass(frozen=True)
class CommandLedgerEvent:
    timestamp_utc: str
    command_id: str
    command: str
    normalized_args: tuple[str, ...]
    goal: str
    status: str
    verification: str
    artifacts_updated: tuple[str, ...]
    error_message: str | None = None


def _tuple_of_strings(value: object) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(str(item) for item in value if str(item).strip())


def read_command_ledger(path: Path = COMMAND_LEDGER_PATH) -> tuple[CommandLedgerEvent, ...]:
    if not path.exists():
        return ()

    events: list[CommandLedgerEvent] = []
    for raw_line in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        payload = json.loads(line)
        events.append(
            CommandLedgerEvent(
                timestamp_utc=str(payload.get("timestamp_utc", "")).strip(),
                command_id=str(payload.get("command_id", "")).strip(),
                command=str(payload.get("command", "")).strip(),
                normalized_args=_tuple_of_strings(payload.get("normalized_args", [])),
                goal=str(payload.get("goal", "")).strip(),
                status=str(payload.get("status", "")).strip(),
                verification=str(payload.get("verification", "")).strip(),
                artifacts_updated=_tuple_of_strings(payload.get("artifacts_updated", [])),
                error_message=(
                    str(payload.get("error_message", "")).strip() or None
                    if payload.get("error_message") is not None
                    else None
                ),
            )
        )
    return tuple(events)


def latest_success_events_by_command(
    events: tuple[CommandLedgerEvent, ...],
) -> dict[str, CommandLedgerEvent]:
    latest_by_command: dict[str, CommandLedgerEvent] = {}
    for event in events:
        if event.status != "ok":
            continue
        latest_by_command[event.command_id] = event
    return latest_by_command
