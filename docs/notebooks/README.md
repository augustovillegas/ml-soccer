# Inventario de Notebooks Oficiales

> Archivo generado automaticamente desde `config/project_governance.toml`.
> Regenerar con `.\scripts\sync-project.ps1` cuando cambie el manifiesto o un notebook oficial.

## 01 - explorer / matchhistory

- Notebook ID: `explorer_matchhistory`
- Notebook: [01_explorer_matchhistory.ipynb](../../notebooks/01_explorer_matchhistory.ipynb)
- Export Markdown: [01_explorer_matchhistory_cells.md](./01_explorer_matchhistory_cells.md)
- Stage: `explorer`
- Topic: `matchhistory`
- Template profile: `official_v1`
- Source dataset ids: `(ninguno)`
- Output dataset ids: `matchhistory_bronze_matches`

## 02 - silver / matchhistory

- Notebook ID: `silver_matchhistory`
- Notebook: [02_silver_matchhistory.ipynb](../../notebooks/02_silver_matchhistory.ipynb)
- Export Markdown: [02_silver_matchhistory_cells.md](./02_silver_matchhistory_cells.md)
- Stage: `silver`
- Topic: `matchhistory`
- Template profile: `official_v1`
- Source dataset ids: `matchhistory_bronze_matches`
- Output dataset ids: `matchhistory_silver_matches`
