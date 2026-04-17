from __future__ import annotations

from argparse import ArgumentParser
from fnmatch import fnmatch
from pathlib import Path
import subprocess
import sys
import time

from football_ml.governance import ProjectGovernance, load_project_governance
from football_ml.sync_project import sync_project


def parse_args() -> ArgumentParser:
    parser = ArgumentParser(description="Watcher local para resincronizar artefactos gobernados del proyecto.")
    parser.add_argument(
        "--skip-initial-sync",
        action="store_true",
        help="No ejecuta una resincronizacion completa al iniciar.",
    )
    parser.add_argument(
        "--debounce-seconds",
        type=float,
        help="Sobrescribe el debounce configurado en project_governance.toml.",
    )
    return parser


def _normalize_path(path: Path, governance: ProjectGovernance) -> str | None:
    try:
        return path.resolve().relative_to(governance.project_root.resolve()).as_posix()
    except ValueError:
        return None


def _matched_actions(governance: ProjectGovernance, changed_paths: set[str]) -> set[str]:
    actions: set[str] = set()
    for rule in governance.watcher.rules:
        if any(fnmatch(changed_path, pattern) for changed_path in changed_paths for pattern in rule.patterns):
            actions.update(rule.actions)
    return actions


def _run_quick_validate() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "football_ml.validate", "--scope", "project"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        print(result.stdout.strip())
        return

    print(result.stdout.strip())
    print(result.stderr.strip())


def _watchdog_import():
    try:
        from watchdog.events import FileSystemEventHandler
        from watchdog.observers import Observer
    except ImportError as exc:  # pragma: no cover - guard path
        raise RuntimeError(
            "Falta la dependencia 'watchdog'. Ejecuta '.\\scripts\\sync-project.ps1' y luego instala dependencias con bootstrap."
        ) from exc
    return FileSystemEventHandler, Observer


def main() -> int:
    args = parse_args().parse_args()
    governance = load_project_governance()
    debounce_seconds = args.debounce_seconds or governance.watcher.debounce_seconds

    if not args.skip_initial_sync:
        sync_project(changed_paths=[])

    FileSystemEventHandler, Observer = _watchdog_import()
    pending_paths: set[str] = set()
    last_event_at = 0.0

    class ProjectEventHandler(FileSystemEventHandler):
        def _register(self, raw_path: str) -> None:
            nonlocal last_event_at
            normalized = _normalize_path(Path(raw_path), governance)
            if normalized is None:
                return
            pending_paths.add(normalized)
            last_event_at = time.monotonic()

        def on_modified(self, event) -> None:  # pragma: no cover - event bridge
            if not event.is_directory:
                self._register(event.src_path)

        def on_created(self, event) -> None:  # pragma: no cover - event bridge
            if not event.is_directory:
                self._register(event.src_path)

        def on_moved(self, event) -> None:  # pragma: no cover - event bridge
            if not event.is_directory:
                self._register(event.src_path)
                self._register(event.dest_path)

        def on_deleted(self, event) -> None:  # pragma: no cover - event bridge
            if not event.is_directory:
                self._register(event.src_path)

    observer = Observer()
    handler = ProjectEventHandler()
    scheduled_roots: set[Path] = set()

    for watched_path in governance.watcher.watched_paths:
        absolute_path = (governance.project_root / watched_path).resolve()
        schedule_root = absolute_path if absolute_path.is_dir() else absolute_path.parent
        if schedule_root in scheduled_roots:
            continue
        scheduled_roots.add(schedule_root)
        observer.schedule(handler, str(schedule_root), recursive=True)

    observer.start()
    print(f"Watcher activo sobre {len(scheduled_roots)} roots. Debounce={debounce_seconds}s")

    try:
        while True:  # pragma: no branch - long-running watcher
            if pending_paths and (time.monotonic() - last_event_at) >= debounce_seconds:
                changed_paths = sorted(pending_paths)
                pending_paths.clear()
                synced_paths = sync_project(changed_paths=changed_paths)
                if synced_paths:
                    print("Artifacts synchronized:")
                    for path in synced_paths:
                        print(f"- {path}")
                actions = _matched_actions(governance, set(changed_paths))
                if "quick_validate" in actions:
                    _run_quick_validate()
            time.sleep(0.25)
    except KeyboardInterrupt:
        pass
    finally:
        observer.stop()
        observer.join()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
