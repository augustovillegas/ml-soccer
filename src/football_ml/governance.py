from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
import tomllib


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = PROJECT_ROOT / "config"
PROJECT_GOVERNANCE_PATH = CONFIG_DIR / "project_governance.toml"
SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:_[a-z0-9]+)*$")
WATCHER_ACTIONS = {
    "generated_docs",
    "notebook_exports_all",
    "notebook_exports_changed",
    "notebooks_index",
    "quick_validate",
    "requirements",
}
DEFAULT_DOC_CLASSES = ("generated", "guide", "notebook_export", "research", "ledger")
DEFAULT_LIVE_STATE_ALLOWED_CLASSES = ("generated", "ledger", "notebook_export")


@dataclass(frozen=True)
class GovernedEnvironment:
    python_version: str
    kernel_name: str
    kernel_display_name: str
    notebooks_dir: Path
    notebook_docs_dir: Path


@dataclass(frozen=True)
class ManagedNotebook:
    notebook_id: str
    order: int
    stage: str
    topic: str
    notebook_path: Path
    doc_path: Path
    template_profile: str
    source_dataset_ids: tuple[str, ...]
    output_dataset_ids: tuple[str, ...]


@dataclass(frozen=True)
class WatcherRule:
    rule_id: str
    patterns: tuple[str, ...]
    actions: tuple[str, ...]


@dataclass(frozen=True)
class WatcherConfig:
    debounce_seconds: float
    watched_paths: tuple[str, ...]
    rules: tuple[WatcherRule, ...]


@dataclass(frozen=True)
class OfficialCommand:
    order: int
    command_id: str
    script_path: Path
    purpose: str
    verification: str
    impacted_artifacts: tuple[str, ...]
    document_in_bitacora: bool


@dataclass(frozen=True)
class GeneratedDoc:
    doc_id: str
    path: Path
    generator: str
    doc_class: str
    source_paths: tuple[str, ...]


@dataclass(frozen=True)
class DocRules:
    allowed_doc_classes: tuple[str, ...]
    live_state_allowed_classes: tuple[str, ...]


@dataclass(frozen=True)
class ProjectGovernance:
    project_root: Path
    config_path: Path
    environment: GovernedEnvironment
    notebooks: tuple[ManagedNotebook, ...]
    watcher: WatcherConfig
    official_commands: tuple[OfficialCommand, ...]
    generated_docs: tuple[GeneratedDoc, ...]
    doc_rules: DocRules


def slugify_token(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", value.lower())
    return slug.strip("_")


def _resolve_project_path(raw_path: str, project_root: Path) -> Path:
    path = Path(raw_path)
    if path.is_absolute():
        return path
    return project_root / path


def _ensure_slug(value: str, field_name: str) -> str:
    if not SLUG_PATTERN.match(value):
        raise ValueError(
            f"{field_name} debe ser un slug en snake_case con solo letras minusculas, numeros y '_' ({value!r})."
        )
    return value


def _load_environment(raw_environment: dict[str, object], project_root: Path) -> GovernedEnvironment:
    return GovernedEnvironment(
        python_version=str(raw_environment["python_version"]),
        kernel_name=str(raw_environment["kernel_name"]),
        kernel_display_name=str(raw_environment["kernel_display_name"]),
        notebooks_dir=_resolve_project_path(str(raw_environment["notebooks_dir"]), project_root),
        notebook_docs_dir=_resolve_project_path(str(raw_environment["notebook_docs_dir"]), project_root),
    )


def _load_notebook(raw_notebook: dict[str, object], project_root: Path) -> ManagedNotebook:
    source_dataset_ids = tuple(str(item) for item in raw_notebook.get("source_dataset_ids", []))
    output_dataset_ids = tuple(str(item) for item in raw_notebook.get("output_dataset_ids", []))
    notebook_id = _ensure_slug(str(raw_notebook["notebook_id"]), "notebook_id")
    stage = _ensure_slug(str(raw_notebook["stage"]), "stage")
    topic = _ensure_slug(str(raw_notebook["topic"]), "topic")

    return ManagedNotebook(
        notebook_id=notebook_id,
        order=int(raw_notebook["order"]),
        stage=stage,
        topic=topic,
        notebook_path=_resolve_project_path(str(raw_notebook["path"]), project_root),
        doc_path=_resolve_project_path(str(raw_notebook["doc_path"]), project_root),
        template_profile=str(raw_notebook["template_profile"]),
        source_dataset_ids=source_dataset_ids,
        output_dataset_ids=output_dataset_ids,
    )


def _load_watcher_rule(raw_rule: dict[str, object]) -> WatcherRule:
    rule_id = _ensure_slug(str(raw_rule["rule_id"]), "watcher.rule_id")
    patterns = tuple(str(item).strip() for item in raw_rule.get("patterns", []) if str(item).strip())
    actions = tuple(str(item).strip() for item in raw_rule.get("actions", []) if str(item).strip())
    return WatcherRule(rule_id=rule_id, patterns=patterns, actions=actions)


def _load_watcher(raw_watcher: dict[str, object] | None) -> WatcherConfig:
    watcher_data = raw_watcher or {}
    watched_paths = tuple(
        str(item).replace("\\", "/").strip()
        for item in watcher_data.get("watched_paths", [])
        if str(item).strip()
    )
    rules = tuple(_load_watcher_rule(item) for item in watcher_data.get("rules", []))
    return WatcherConfig(
        debounce_seconds=float(watcher_data.get("debounce_seconds", 1.5)),
        watched_paths=watched_paths,
        rules=rules,
    )


def _load_official_command(raw_command: dict[str, object], project_root: Path) -> OfficialCommand:
    command_id = _ensure_slug(str(raw_command["command_id"]), "official_commands.command_id")
    impacted_artifacts = tuple(
        str(item).replace("\\", "/").strip()
        for item in raw_command.get("impacted_artifacts", [])
        if str(item).strip()
    )
    return OfficialCommand(
        order=int(raw_command["order"]),
        command_id=command_id,
        script_path=_resolve_project_path(str(raw_command["script_path"]), project_root),
        purpose=str(raw_command["purpose"]).strip(),
        verification=str(raw_command["verification"]).strip(),
        impacted_artifacts=impacted_artifacts,
        document_in_bitacora=bool(raw_command.get("document_in_bitacora", False)),
    )


def _load_generated_doc(raw_doc: dict[str, object], project_root: Path) -> GeneratedDoc:
    doc_id = _ensure_slug(str(raw_doc["doc_id"]), "generated_docs.doc_id")
    doc_class = str(raw_doc["doc_class"]).strip()
    source_paths = tuple(
        str(item).replace("\\", "/").strip()
        for item in raw_doc.get("source_paths", [])
        if str(item).strip()
    )
    return GeneratedDoc(
        doc_id=doc_id,
        path=_resolve_project_path(str(raw_doc["path"]), project_root),
        generator=str(raw_doc["generator"]).strip(),
        doc_class=doc_class,
        source_paths=source_paths,
    )


def _load_doc_rules(raw_doc_rules: dict[str, object] | None) -> DocRules:
    doc_rules_data = raw_doc_rules or {}
    allowed_doc_classes = tuple(
        str(item).strip()
        for item in doc_rules_data.get("allowed_doc_classes", DEFAULT_DOC_CLASSES)
        if str(item).strip()
    )
    live_state_allowed_classes = tuple(
        str(item).strip()
        for item in doc_rules_data.get(
            "live_state_allowed_classes",
            DEFAULT_LIVE_STATE_ALLOWED_CLASSES,
        )
        if str(item).strip()
    )
    return DocRules(
        allowed_doc_classes=allowed_doc_classes,
        live_state_allowed_classes=live_state_allowed_classes,
    )


def _manifest_issues(governance: ProjectGovernance) -> list[str]:
    issues: list[str] = []

    if not governance.notebooks:
        issues.append("project_governance.toml debe registrar al menos un notebook oficial.")
    else:
        notebook_ids = [entry.notebook_id for entry in governance.notebooks]
        orders = [entry.order for entry in governance.notebooks]
        notebook_paths = [entry.notebook_path.resolve() for entry in governance.notebooks]
        doc_paths = [entry.doc_path.resolve() for entry in governance.notebooks]

        duplicate_ids = sorted({item for item in notebook_ids if notebook_ids.count(item) > 1})
        if duplicate_ids:
            issues.append(f"Los notebooks oficiales no deben repetir notebook_id: {duplicate_ids}.")

        duplicate_orders = sorted({item for item in orders if orders.count(item) > 1})
        if duplicate_orders:
            issues.append(f"Los notebooks oficiales no deben repetir order: {duplicate_orders}.")

        duplicate_notebook_paths = sorted(
            {
                str(path.relative_to(governance.project_root))
                for path in notebook_paths
                if notebook_paths.count(path) > 1
            }
        )
        if duplicate_notebook_paths:
            issues.append(f"Los notebooks oficiales no deben repetir path: {duplicate_notebook_paths}.")

        duplicate_doc_paths = sorted(
            {
                str(path.relative_to(governance.project_root))
                for path in doc_paths
                if doc_paths.count(path) > 1
            }
        )
        if duplicate_doc_paths:
            issues.append(f"Los notebooks oficiales no deben repetir doc_path: {duplicate_doc_paths}.")

        for entry in governance.notebooks:
            expected_prefix = f"{entry.order:02d}_"
            if not entry.notebook_path.name.startswith(expected_prefix):
                issues.append(
                    f"{entry.notebook_path}: el nombre del notebook debe empezar con '{expected_prefix}'."
                )
            if entry.notebook_path.parent.resolve() != governance.environment.notebooks_dir.resolve():
                issues.append(
                    f"{entry.notebook_path}: todo notebook oficial debe vivir en '{governance.environment.notebooks_dir}'."
                )
            if entry.doc_path.parent.resolve() != governance.environment.notebook_docs_dir.resolve():
                issues.append(
                    f"{entry.doc_path}: todo export oficial debe vivir en '{governance.environment.notebook_docs_dir}'."
                )
            if entry.template_profile != "official_v1":
                issues.append(
                    f"{entry.notebook_id}: template_profile no soportado '{entry.template_profile}'."
                )
            if entry.order < 1:
                issues.append(f"{entry.notebook_id}: order debe ser >= 1.")

    command_ids = [entry.command_id for entry in governance.official_commands]
    command_orders = [entry.order for entry in governance.official_commands]
    command_paths = [entry.script_path.resolve() for entry in governance.official_commands]
    duplicate_command_ids = sorted({item for item in command_ids if command_ids.count(item) > 1})
    if duplicate_command_ids:
        issues.append(f"Los comandos oficiales no deben repetir command_id: {duplicate_command_ids}.")
    duplicate_command_orders = sorted({item for item in command_orders if command_orders.count(item) > 1})
    if duplicate_command_orders:
        issues.append(f"Los comandos oficiales no deben repetir order: {duplicate_command_orders}.")
    duplicate_command_paths = sorted(
        {
            str(path.relative_to(governance.project_root))
            for path in command_paths
            if command_paths.count(path) > 1
        }
    )
    if duplicate_command_paths:
        issues.append(f"Los comandos oficiales no deben repetir script_path: {duplicate_command_paths}.")
    for entry in governance.official_commands:
        if entry.order < 1:
            issues.append(f"{entry.command_id}: order debe ser >= 1.")
        if not entry.purpose:
            issues.append(f"{entry.command_id}: purpose no puede ser vacio.")
        if not entry.verification:
            issues.append(f"{entry.command_id}: verification no puede ser vacio.")
        if entry.script_path.suffix.lower() != ".ps1":
            issues.append(f"{entry.command_id}: script_path debe apuntar a un .ps1 y no a '{entry.script_path}'.")

    generated_doc_ids = [entry.doc_id for entry in governance.generated_docs]
    generated_doc_paths = [entry.path.resolve() for entry in governance.generated_docs]
    duplicate_generated_doc_ids = sorted(
        {item for item in generated_doc_ids if generated_doc_ids.count(item) > 1}
    )
    if duplicate_generated_doc_ids:
        issues.append(f"Los documentos generados no deben repetir doc_id: {duplicate_generated_doc_ids}.")
    duplicate_generated_doc_paths = sorted(
        {
            str(path.relative_to(governance.project_root))
            for path in generated_doc_paths
            if generated_doc_paths.count(path) > 1
        }
    )
    if duplicate_generated_doc_paths:
        issues.append(f"Los documentos generados no deben repetir path: {duplicate_generated_doc_paths}.")
    for entry in governance.generated_docs:
        if entry.doc_class not in governance.doc_rules.allowed_doc_classes:
            issues.append(
                f"{entry.doc_id}: doc_class '{entry.doc_class}' no esta permitido por doc_rules."
            )
        if not entry.generator:
            issues.append(f"{entry.doc_id}: generator no puede ser vacio.")

    live_state_not_allowed = sorted(
        set(governance.doc_rules.live_state_allowed_classes) - set(governance.doc_rules.allowed_doc_classes)
    )
    if live_state_not_allowed:
        issues.append(
            "doc_rules.live_state_allowed_classes debe ser subconjunto de allowed_doc_classes: "
            f"{live_state_not_allowed}."
        )

    for rule in governance.watcher.rules:
        if not rule.patterns:
            issues.append(f"{rule.rule_id}: watcher.rules.patterns no puede ser vacio.")
        if not rule.actions:
            issues.append(f"{rule.rule_id}: watcher.rules.actions no puede ser vacio.")
        invalid_actions = sorted(set(rule.actions) - WATCHER_ACTIONS)
        if invalid_actions:
            issues.append(f"{rule.rule_id}: watcher.rules.actions no soportadas: {invalid_actions}.")

    return issues


def load_project_governance(
    config_path: Path | None = None,
    project_root: Path | None = None,
) -> ProjectGovernance:
    effective_project_root = (project_root or PROJECT_ROOT).resolve()
    effective_config_path = (config_path or (effective_project_root / "config" / "project_governance.toml")).resolve()
    payload = tomllib.loads(effective_config_path.read_text(encoding="utf-8"))
    environment = _load_environment(payload["environment"], effective_project_root)
    notebooks = tuple(
        sorted(
            (_load_notebook(item, effective_project_root) for item in payload.get("notebooks", [])),
            key=lambda entry: entry.order,
        )
    )
    governance = ProjectGovernance(
        project_root=effective_project_root,
        config_path=effective_config_path,
        environment=environment,
        notebooks=notebooks,
        watcher=_load_watcher(payload.get("watcher")),
        official_commands=tuple(
            sorted(
                (
                    _load_official_command(item, effective_project_root)
                    for item in payload.get("official_commands", [])
                ),
                key=lambda entry: entry.order,
            )
        ),
        generated_docs=tuple(
            _load_generated_doc(item, effective_project_root)
            for item in payload.get("generated_docs", [])
        ),
        doc_rules=_load_doc_rules(payload.get("doc_rules")),
    )
    issues = _manifest_issues(governance)
    if issues:
        raise ValueError(" ".join(issues))
    return governance


def next_notebook_order(governance: ProjectGovernance) -> int:
    if not governance.notebooks:
        return 1
    return max(entry.order for entry in governance.notebooks) + 1


def _toml_value(value: object) -> str:
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return f"{value:.1f}".rstrip("0").rstrip(".")
    if isinstance(value, (tuple, list)):
        return "[" + ", ".join(_toml_value(item) for item in value) + "]"
    raise TypeError(f"Valor TOML no soportado: {value!r}")


def _relative_to_root(path: Path, project_root: Path) -> str:
    return path.resolve().relative_to(project_root.resolve()).as_posix()


def render_project_governance_toml(governance: ProjectGovernance) -> str:
    environment = governance.environment
    lines = [
        "[environment]",
        f"python_version = {_toml_value(environment.python_version)}",
        f"kernel_name = {_toml_value(environment.kernel_name)}",
        f"kernel_display_name = {_toml_value(environment.kernel_display_name)}",
        f"notebooks_dir = {_toml_value(_relative_to_root(environment.notebooks_dir, governance.project_root))}",
        f"notebook_docs_dir = {_toml_value(_relative_to_root(environment.notebook_docs_dir, governance.project_root))}",
        "",
        "[watcher]",
        f"debounce_seconds = {_toml_value(governance.watcher.debounce_seconds)}",
        f"watched_paths = {_toml_value(governance.watcher.watched_paths)}",
        "",
    ]

    for rule in governance.watcher.rules:
        lines.extend(
            [
                "[[watcher.rules]]",
                f"rule_id = {_toml_value(rule.rule_id)}",
                f"patterns = {_toml_value(rule.patterns)}",
                f"actions = {_toml_value(rule.actions)}",
                "",
            ]
        )

    lines.extend(
        [
            "[doc_rules]",
            f"allowed_doc_classes = {_toml_value(governance.doc_rules.allowed_doc_classes)}",
            f"live_state_allowed_classes = {_toml_value(governance.doc_rules.live_state_allowed_classes)}",
            "",
        ]
    )

    for entry in sorted(governance.official_commands, key=lambda command: command.order):
        lines.extend(
            [
                "[[official_commands]]",
                f"order = {entry.order}",
                f"command_id = {_toml_value(entry.command_id)}",
                f"script_path = {_toml_value(_relative_to_root(entry.script_path, governance.project_root))}",
                f"purpose = {_toml_value(entry.purpose)}",
                f"verification = {_toml_value(entry.verification)}",
                f"impacted_artifacts = {_toml_value(entry.impacted_artifacts)}",
                f"document_in_bitacora = {_toml_value(entry.document_in_bitacora)}",
                "",
            ]
        )

    for entry in governance.generated_docs:
        lines.extend(
            [
                "[[generated_docs]]",
                f"doc_id = {_toml_value(entry.doc_id)}",
                f"path = {_toml_value(_relative_to_root(entry.path, governance.project_root))}",
                f"generator = {_toml_value(entry.generator)}",
                f"doc_class = {_toml_value(entry.doc_class)}",
                f"source_paths = {_toml_value(entry.source_paths)}",
                "",
            ]
        )

    for entry in sorted(governance.notebooks, key=lambda notebook: notebook.order):
        lines.extend(
            [
                "[[notebooks]]",
                f"notebook_id = {_toml_value(entry.notebook_id)}",
                f"order = {entry.order}",
                f"stage = {_toml_value(entry.stage)}",
                f"topic = {_toml_value(entry.topic)}",
                f"path = {_toml_value(_relative_to_root(entry.notebook_path, governance.project_root))}",
                f"doc_path = {_toml_value(_relative_to_root(entry.doc_path, governance.project_root))}",
                f"template_profile = {_toml_value(entry.template_profile)}",
                f"source_dataset_ids = {_toml_value(entry.source_dataset_ids)}",
                f"output_dataset_ids = {_toml_value(entry.output_dataset_ids)}",
                "",
            ]
        )

    return "\n".join(lines).rstrip() + "\n"


def write_project_governance(governance: ProjectGovernance, config_path: Path | None = None) -> Path:
    target_path = (config_path or governance.config_path).resolve()
    target_path.write_text(render_project_governance_toml(governance), encoding="utf-8")
    return target_path
