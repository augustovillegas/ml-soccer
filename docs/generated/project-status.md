# Estado Operativo Generado

> Archivo generado automaticamente desde `config/project_governance.toml + config/ingestion.toml + datasets/manifests locales`.

## Resumen

- Python gobernado: `3.13`
- Kernel oficial: `football-ml (.venv)`
- Watcher debounce: `1.5` segundos
- Tarea oficial MatchHistory: `football-ml-refresh-matchhistory` a las `09:00`
- Temporadas gobernadas MatchHistory: `2122, 2223, 2324`

## Notebooks oficiales

- `explorer_matchhistory` -> `notebooks/01_explorer_matchhistory.ipynb` | doc=`docs/notebooks/01_explorer_matchhistory_cells.md` | outputs=`matchhistory_bronze_matches`
- `silver_matchhistory` -> `notebooks/02_silver_matchhistory.ipynb` | doc=`docs/notebooks/02_silver_matchhistory_cells.md` | outputs=`matchhistory_silver_matches`

## Datasets oficiales locales

- `matchhistory_bronze_matches` -> `data/bronze/matchhistory/raw/matches_bronze.parquet` | rows=`1140` | columns=`27`
- `matchhistory_silver_matches` -> `data/silver/matches_silver.parquet` | rows=`1140` | columns=`25`

## Estado MatchHistory por temporada

- `2122`: status=`no_change_manual` | source_mode=`manual_csv` | row_count=`380` | column_count=`106`
- `2223`: status=`no_change_manual` | source_mode=`manual_csv` | row_count=`380` | column_count=`106`
- `2324`: status=`no_change_manual` | source_mode=`manual_csv` | row_count=`380` | column_count=`106`
