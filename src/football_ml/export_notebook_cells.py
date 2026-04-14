from __future__ import annotations

from argparse import ArgumentParser
from hashlib import sha256
import json
from json import JSONDecodeError
from pathlib import Path
import re

from football_ml.paths import (
    NOTEBOOK_CELLS_DOC_PATH,
    NOTEBOOK_PATH,
    ManagedNotebook,
    ensure_dir,
    iter_managed_notebooks,
    relative_to_project,
)


DEFAULT_EXPLANATION = "Codigo de la celda original sin cambios."
DEFAULT_OUTPUT_TEXT = "Sin output guardado en el notebook."
SOURCE_MARKER_PREFIX = "<!-- notebook-source: "
HASH_MARKER_PREFIX = "<!-- notebook-code-and-outputs-sha256: "
MARKER_SUFFIX = " -->"


def parse_args() -> ArgumentParser:
    parser = ArgumentParser(description="Exporta las celdas de codigo de notebooks oficiales gestionados a Markdown.")
    parser.add_argument("--notebook-path", help="Ruta al notebook fuente.")
    parser.add_argument("--output-path", help="Ruta del Markdown generado.")
    parser.add_argument(
        "--all",
        action="store_true",
        help="Exporta todos los notebooks oficiales gestionados por el proyecto.",
    )
    return parser


def _effective_managed_notebooks(
    managed_notebooks: tuple[ManagedNotebook, ...] | None = None,
) -> tuple[ManagedNotebook, ...]:
    return managed_notebooks if managed_notebooks is not None else iter_managed_notebooks()


def _managed_notebook_doc_map(
    managed_notebooks: tuple[ManagedNotebook, ...] | None = None,
) -> dict[Path, Path]:
    return {
        entry.notebook_path.resolve(): entry.doc_path.resolve()
        for entry in _effective_managed_notebooks(managed_notebooks)
    }


def resolve_output_path_for_notebook(
    notebook_path: Path,
    managed_notebooks: tuple[ManagedNotebook, ...] | None = None,
) -> Path:
    notebook_key = notebook_path.resolve()
    managed_doc_map = _managed_notebook_doc_map(managed_notebooks)

    if notebook_key in managed_doc_map:
        return managed_doc_map[notebook_key]

    raise ValueError(
        "Debes indicar --output-path cuando el notebook fuente no forma parte de los notebooks oficiales gestionados."
    )


def load_notebook_payload(notebook_path: Path) -> dict[str, object]:
    try:
        return json.loads(notebook_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"No existe el notebook fuente '{notebook_path}'.") from exc
    except JSONDecodeError as exc:
        raise ValueError(f"El notebook '{notebook_path}' no es JSON valido: {exc}") from exc


def iter_code_cells(payload: dict[str, object]) -> list[dict[str, object]]:
    raw_cells = payload.get("cells", [])
    if not isinstance(raw_cells, list):
        raise ValueError("El notebook no tiene una lista valida de celdas.")
    return [cell for cell in raw_cells if isinstance(cell, dict) and cell.get("cell_type") == "code"]


def cell_source_text(cell: dict[str, object]) -> str:
    source = cell.get("source", [])
    if isinstance(source, str):
        return source
    if isinstance(source, list):
        return "".join(str(line) for line in source)
    raise ValueError("La celda tiene un campo 'source' invalido.")


def _text_from_notebook_value(value: object) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "".join(str(item) for item in value)
    return str(value)


def extract_cell_outputs(cell: dict[str, object]) -> list[str]:
    rendered_outputs: list[str] = []
    raw_outputs = cell.get("outputs", [])

    if not isinstance(raw_outputs, list):
        return rendered_outputs

    for output in raw_outputs:
        if not isinstance(output, dict):
            continue

        output_type = output.get("output_type")

        if output_type == "stream":
            text = _text_from_notebook_value(output.get("text", ""))
            if text.strip():
                rendered_outputs.append(text.rstrip())
            continue

        if output_type in {"display_data", "execute_result"}:
            data = output.get("data", {})
            if not isinstance(data, dict):
                continue

            if "text/plain" in data:
                text = _text_from_notebook_value(data["text/plain"])
                if text.strip():
                    rendered_outputs.append(text.rstrip())
                continue

            if "text/markdown" in data:
                text = _text_from_notebook_value(data["text/markdown"])
                if text.strip():
                    rendered_outputs.append(text.rstrip())
                continue

            if "application/json" in data:
                text = json.dumps(data["application/json"], ensure_ascii=False, indent=2)
                if text.strip():
                    rendered_outputs.append(text.rstrip())
                continue

        if output_type == "error":
            traceback = output.get("traceback")
            if isinstance(traceback, list) and traceback:
                rendered_outputs.append(_text_from_notebook_value(traceback).rstrip())
                continue

            ename = str(output.get("ename", "Error"))
            evalue = str(output.get("evalue", "")).strip()
            rendered_outputs.append(f"{ename}: {evalue}".rstrip(": ").rstrip())

    return rendered_outputs


def compute_notebook_code_cells_sha256(payload: dict[str, object]) -> str:
    code_and_outputs = [
        {
            "source": cell_source_text(cell),
            "outputs": extract_cell_outputs(cell),
        }
        for cell in iter_code_cells(payload)
    ]
    content = json.dumps(code_and_outputs, ensure_ascii=False)
    return sha256(content.encode("utf-8")).hexdigest()


def _is_separator_line(text: str) -> bool:
    return bool(text) and all(character in "=*-_~`" for character in text)


def extract_cell_explanation(source_text: str) -> str:
    explanations: list[str] = []

    for raw_line in source_text.splitlines():
        stripped = raw_line.strip()

        if not stripped:
            continue
        if not stripped.startswith("#"):
            break

        comment = stripped.lstrip("#").strip()
        if not comment or _is_separator_line(comment):
            continue
        explanations.append(comment)

    if not explanations:
        return DEFAULT_EXPLANATION

    explanation = " ".join(explanations)
    return re.sub(r"\s+", " ", explanation).strip()


def source_marker_value(notebook_path: Path) -> str:
    return relative_to_project(notebook_path).as_posix()


def source_marker_line(notebook_path: Path) -> str:
    return f"{SOURCE_MARKER_PREFIX}{source_marker_value(notebook_path)}{MARKER_SUFFIX}"


def hash_marker_line(payload: dict[str, object]) -> str:
    return f"{HASH_MARKER_PREFIX}{compute_notebook_code_cells_sha256(payload)}{MARKER_SUFFIX}"


def extract_marker_value(markdown_text: str, prefix: str) -> str | None:
    for line in markdown_text.splitlines():
        if line.startswith(prefix) and line.endswith(MARKER_SUFFIX):
            return line[len(prefix) : -len(MARKER_SUFFIX)]
    return None


def render_markdown(notebook_path: Path, payload: dict[str, object]) -> str:
    sections: list[str] = [
        f"# Codigo de Celdas del Notebook: {notebook_path.name}",
        "",
        f"> Archivo generado automaticamente desde `{relative_to_project(notebook_path).as_posix()}`.",
        "> Regenerar con `.\\scripts\\export-notebook-cells.ps1` cuando cambie el notebook fuente.",
        "",
        source_marker_line(notebook_path),
        hash_marker_line(payload),
        "",
    ]

    for index, cell in enumerate(iter_code_cells(payload), start=1):
        cell_id = str(cell.get("id") or f"cell-{index}")
        source_text = cell_source_text(cell).rstrip()
        explanation = extract_cell_explanation(source_text)
        output_texts = extract_cell_outputs(cell)

        sections.extend(
            [
                f"## Cell {index} - {cell_id}",
                "",
                f"**Explicacion:** {explanation}",
                "",
                "```python",
                source_text,
                "```",
                "",
            ]
        )

        if output_texts:
            for output_index, output_text in enumerate(output_texts, start=1):
                sections.extend(
                    [
                        f"**Output {output_index}:**",
                        "",
                        "```text",
                        output_text,
                        "```",
                        "",
                    ]
                )
        else:
            sections.extend(
                [
                    f"**Output:** {DEFAULT_OUTPUT_TEXT}",
                    "",
                ]
            )

    return "\n".join(sections).rstrip() + "\n"


def export_notebook_cells(notebook_path: Path = NOTEBOOK_PATH, output_path: Path = NOTEBOOK_CELLS_DOC_PATH) -> Path:
    payload = load_notebook_payload(notebook_path)
    ensure_dir(output_path.parent)
    output_path.write_text(render_markdown(notebook_path, payload), encoding="utf-8")
    return output_path


def export_all_managed_notebooks(
    managed_notebooks: tuple[ManagedNotebook, ...] | None = None,
) -> list[Path]:
    exported_paths: list[Path] = []

    for entry in _effective_managed_notebooks(managed_notebooks):
        exported_paths.append(export_notebook_cells(entry.notebook_path, entry.doc_path))

    return exported_paths


def check_generated_markdown_sync(
    notebook_path: Path = NOTEBOOK_PATH,
    output_path: Path = NOTEBOOK_CELLS_DOC_PATH,
) -> list[str]:
    issues: list[str] = []

    if not output_path.exists():
        return [f"Falta el Markdown generado del notebook: {output_path}"]

    payload = load_notebook_payload(notebook_path)
    markdown_text = output_path.read_text(encoding="utf-8")
    expected_source = source_marker_value(notebook_path)
    expected_hash = compute_notebook_code_cells_sha256(payload)
    actual_source = extract_marker_value(markdown_text, SOURCE_MARKER_PREFIX)
    actual_hash = extract_marker_value(markdown_text, HASH_MARKER_PREFIX)

    if actual_source != expected_source:
        issues.append(
            f"{output_path}: el marker de notebook fuente debe ser '{expected_source}' y no '{actual_source}'."
        )
    if actual_hash != expected_hash:
        issues.append(
            f"{output_path}: el Markdown generado esta desactualizado respecto del notebook fuente."
        )
    return issues


def main() -> int:
    args = parse_args().parse_args()

    try:
        if args.all or (not args.notebook_path and not args.output_path):
            exported_paths = export_all_managed_notebooks()
            print("Notebook cells exported to:")
            for exported_path in exported_paths:
                print(f"- {exported_path}")
            return 0

        if args.output_path and not args.notebook_path:
            raise ValueError("Debes indicar --notebook-path cuando usas --output-path.")

        notebook_path = Path(args.notebook_path).resolve() if args.notebook_path else NOTEBOOK_PATH.resolve()
        output_path = (
            Path(args.output_path).resolve()
            if args.output_path
            else resolve_output_path_for_notebook(notebook_path)
        )

        exported_path = export_notebook_cells(notebook_path=notebook_path, output_path=output_path)
    except Exception as exc:
        print(str(exc))
        return 1

    print(f"Notebook cells exported to: {exported_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
