from __future__ import annotations

from argparse import ArgumentParser
from dataclasses import replace
import json
from pathlib import Path
import sys

from football_ml.governance import (
    ManagedNotebook,
    ProjectGovernance,
    load_project_governance,
    next_notebook_order,
    slugify_token,
    write_project_governance,
)
from football_ml.sync_project import sync_project


def parse_args() -> ArgumentParser:
    parser = ArgumentParser(description="Crea un notebook oficial nuevo y lo registra en el manifiesto de gobernanza.")
    parser.add_argument("--stage", required=True, help="Stage del notebook oficial, por ejemplo 'silver'.")
    parser.add_argument("--topic", required=True, help="Tema del notebook oficial, por ejemplo 'odds_matchhistory'.")
    parser.add_argument("--notebook-id", help="Identificador estable del notebook. Si se omite, se deriva de stage y topic.")
    parser.add_argument(
        "--template-profile",
        default="official_v1",
        help="Perfil de plantilla para el notebook. Actualmente solo se soporta 'official_v1'.",
    )
    parser.add_argument(
        "--source-dataset-id",
        action="append",
        default=[],
        help="Dataset fuente usado por el notebook. Puede repetirse para multiples valores.",
    )
    parser.add_argument(
        "--output-dataset-id",
        action="append",
        default=[],
        help="Dataset de salida producido por el notebook. Puede repetirse para multiples valores.",
    )
    return parser


def _language_info_version(governance: ProjectGovernance) -> str:
    active_version = sys.version.split()[0]
    if active_version.startswith(governance.environment.python_version):
        return active_version
    return f"{governance.environment.python_version}.0"


def _common_bootstrap_source(governance: ProjectGovernance) -> list[str]:
    kernel_display_name = governance.environment.kernel_display_name
    return [
        "# ==============================\n",
        "# 1. Importar librerias basicas\n",
        "# ==============================\n",
        "# `sys` nos permite ver que Python esta usando el notebook.\n",
        "# `Path` sirve para manejar rutas locales del proyecto.\n",
        "# `pandas` queda disponible para explorar datasets locales.\n",
        "\n",
        "import sys\n",
        "from pathlib import Path\n",
        "\n",
        "import pandas as pd\n",
        "\n",
        "# =====================================================\n",
        "# 2. Detectar la raiz del proyecto y validar el kernel\n",
        "# =====================================================\n",
        "# Si abrimos el notebook desde la carpeta `notebooks`, subimos un nivel.\n",
        "# Si no, usamos la carpeta actual como raiz del proyecto.\n",
        "\n",
        'PROJECT_ROOT = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()\n',
        "\n",
        "# Este es el ejecutable correcto del entorno virtual del proyecto.\n",
        'EXPECTED_PYTHON = (PROJECT_ROOT / ".venv" / "Scripts" / "python.exe").resolve()\n',
        "\n",
        "# Si el notebook no esta usando el kernel correcto, frenamos la ejecucion.\n",
        "if Path(sys.executable).resolve() != EXPECTED_PYTHON:\n",
        "    raise RuntimeError(\n",
        f"        \"Kernel incorrecto. Selecciona '{kernel_display_name}'. Ejecutable actual: {sys.executable}\"\n",
        "    )\n",
        "\n",
        "# =============================================\n",
        "# 3. Ajustar configuracion base para explorar\n",
        "# =============================================\n",
        'pd.set_option("display.max_columns", None)\n',
        "\n",
        'print(f"Project root: {PROJECT_ROOT}")\n',
        'print(f"Python exe:   {sys.executable}")\n',
        "\n",
    ]


def build_official_v1_notebook(governance: ProjectGovernance, notebook: ManagedNotebook) -> dict[str, object]:
    cells = [
        {
            "cell_type": "code",
            "execution_count": None,
            "id": "imports-and-kernel-check",
            "metadata": {},
            "outputs": [],
            "source": _common_bootstrap_source(governance),
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "id": "notebook-context",
            "metadata": {},
            "outputs": [],
            "source": [
                "# ==============================\n",
                "# 2. Definir el contexto oficial\n",
                "# ==============================\n",
                "# Esta celda deja visibles los metadatos operativos del notebook.\n",
                "\n",
                f'NOTEBOOK_ID = "{notebook.notebook_id}"\n',
                f'NOTEBOOK_STAGE = "{notebook.stage}"\n',
                f'NOTEBOOK_TOPIC = "{notebook.topic}"\n',
                f"SOURCE_DATASET_IDS = {list(notebook.source_dataset_ids)!r}\n",
                f"OUTPUT_DATASET_IDS = {list(notebook.output_dataset_ids)!r}\n",
                "\n",
                'print(f"Notebook id:        {NOTEBOOK_ID}")\n',
                'print(f"Notebook stage:     {NOTEBOOK_STAGE}")\n',
                'print(f"Notebook topic:     {NOTEBOOK_TOPIC}")\n',
                'print(f"Source datasets:    {SOURCE_DATASET_IDS}")\n',
                'print(f"Output datasets:    {OUTPUT_DATASET_IDS}")\n',
                "\n",
            ],
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "id": "local-paths-and-inputs",
            "metadata": {},
            "outputs": [],
            "source": [
                "# ==============================\n",
                "# 3. Preparar rutas locales base\n",
                "# ==============================\n",
                "# Ajusta aqui las rutas del dataset local que vas a leer en este notebook.\n",
                "\n",
                'DATA_DIR = PROJECT_ROOT / "data"\n',
                'NOTEBOOK_DOCS_DIR = PROJECT_ROOT / "docs" / "notebooks"\n',
                "\n",
                'print(f"Data dir:          {DATA_DIR}")\n',
                'print(f"Notebook docs dir: {NOTEBOOK_DOCS_DIR}")\n',
                "\n",
            ],
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "id": "workbench-placeholder",
            "metadata": {},
            "outputs": [],
            "source": [
                "# ==============================\n",
                "# 4. Area de trabajo inicial\n",
                "# ==============================\n",
                "# Completa este bloque con la lectura local y la logica especifica del notebook.\n",
                "\n",
                "df_preview = pd.DataFrame(\n",
                "    {\n",
                '        "source_dataset_id": SOURCE_DATASET_IDS or ["(ninguno)"],\n',
                '        "output_dataset_id": OUTPUT_DATASET_IDS or ["(ninguno)"],\n',
                "    }\n",
                ")\n",
                "display(df_preview)\n",
                "\n",
            ],
        },
    ]

    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": governance.environment.kernel_display_name,
                "language": "python",
                "name": governance.environment.kernel_name,
            },
            "language_info": {
                "codemirror_mode": {"name": "ipython", "version": 3},
                "file_extension": ".py",
                "mimetype": "text/x-python",
                "name": "python",
                "nbconvert_exporter": "python",
                "pygments_lexer": "ipython3",
                "version": _language_info_version(governance),
            },
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def _template_payload(governance: ProjectGovernance, notebook: ManagedNotebook) -> dict[str, object]:
    if notebook.template_profile != "official_v1":
        raise ValueError(f"Template profile no soportado: {notebook.template_profile}")
    return build_official_v1_notebook(governance, notebook)


def scaffold_notebook(
    stage: str,
    topic: str,
    notebook_id: str | None = None,
    template_profile: str = "official_v1",
    source_dataset_ids: tuple[str, ...] = (),
    output_dataset_ids: tuple[str, ...] = (),
    config_path: Path | None = None,
    project_root: Path | None = None,
) -> tuple[Path, Path, Path]:
    governance = load_project_governance(config_path=config_path, project_root=project_root)
    stage_slug = slugify_token(stage)
    topic_slug = slugify_token(topic)
    derived_notebook_id = slugify_token(notebook_id or f"{stage_slug}_{topic_slug}")
    order = next_notebook_order(governance)
    notebook_name = f"{order:02d}_{stage_slug}_{topic_slug}.ipynb"
    notebook_path = governance.environment.notebooks_dir / notebook_name
    doc_path = governance.environment.notebook_docs_dir / f"{notebook_path.stem}_cells.md"

    if any(entry.notebook_id == derived_notebook_id for entry in governance.notebooks):
        raise ValueError(f"Ya existe un notebook oficial con notebook_id '{derived_notebook_id}'.")
    if notebook_path.exists():
        raise ValueError(f"Ya existe el notebook '{notebook_path}'.")
    if doc_path.exists():
        raise ValueError(f"Ya existe el export Markdown '{doc_path}'.")

    managed_notebook = ManagedNotebook(
        notebook_id=derived_notebook_id,
        order=order,
        stage=stage_slug,
        topic=topic_slug,
        notebook_path=notebook_path,
        doc_path=doc_path,
        template_profile=template_profile,
        source_dataset_ids=tuple(source_dataset_ids),
        output_dataset_ids=tuple(output_dataset_ids),
    )
    payload = _template_payload(governance, managed_notebook)

    notebook_path.parent.mkdir(parents=True, exist_ok=True)
    notebook_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    updated_governance = replace(
        governance,
        notebooks=tuple(sorted((*governance.notebooks, managed_notebook), key=lambda entry: entry.order)),
    )
    write_project_governance(updated_governance, config_path=config_path)
    sync_project(config_path=config_path, project_root=project_root)
    return notebook_path, doc_path, updated_governance.config_path


def main() -> int:
    args = parse_args().parse_args()

    try:
        notebook_path, doc_path, governance_path = scaffold_notebook(
            stage=args.stage,
            topic=args.topic,
            notebook_id=args.notebook_id,
            template_profile=args.template_profile,
            source_dataset_ids=tuple(args.source_dataset_id),
            output_dataset_ids=tuple(args.output_dataset_id),
        )
    except Exception as exc:
        print(str(exc))
        return 1

    print("Notebook scaffolded:")
    print(f"- Notebook: {notebook_path}")
    print(f"- Export Markdown: {doc_path}")
    print(f"- Governance manifest: {governance_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
