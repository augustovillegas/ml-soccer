# Codigo de Celdas del Notebook: 01_explorer_matchhistory.ipynb

> Archivo generado automaticamente desde `notebooks/01_explorer_matchhistory.ipynb`.
> Regenerar con `.\scripts\export-notebook-cells.ps1` cuando cambie el notebook fuente.

<!-- notebook-source: notebooks/01_explorer_matchhistory.ipynb -->
<!-- notebook-code-cells-sha256: 2536c5a899f446843512f393fcc57260d124f5f30d61e9b2c6b4626a916773e8 -->

## Cell 1 - imports-and-kernel-check

**Explicacion:** 1. Importar librerias basicas `sys` nos permite ver que Python esta usando el notebook. `Path` sirve para manejar rutas de archivos de forma clara. `pandas` es la libreria principal para cargar y explorar los CSV.

```python
# ==============================
# 1. Importar librerias basicas
# ==============================
# `sys` nos permite ver que Python esta usando el notebook.
# `Path` sirve para manejar rutas de archivos de forma clara.
# `pandas` es la libreria principal para cargar y explorar los CSV.

import sys
from pathlib import Path

import pandas as pd

# =====================================================
# 2. Detectar la raiz del proyecto y validar el kernel
# =====================================================
# Si abrimos el notebook desde la carpeta `notebooks`, subimos un nivel.
# Si no, usamos la carpeta actual como raiz del proyecto.

PROJECT_ROOT = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()

# Este es el ejecutable correcto del entorno virtual del proyecto.
EXPECTED_PYTHON = (PROJECT_ROOT / ".venv" / "Scripts" / "python.exe").resolve()

# Si el notebook no esta usando el kernel correcto, frenamos la ejecucion.
if Path(sys.executable).resolve() != EXPECTED_PYTHON:
    raise RuntimeError(
        f"Kernel incorrecto. Selecciona 'football-ml (.venv)'. Ejecutable actual: {sys.executable}"
    )

# =============================================
# 3. Importar la configuracion oficial del repo
# =============================================
# Esto evita hardcodear rutas manualmente en el notebook.

from football_ml.config import load_ingestion_config

# =====================================
# 4. Ajustar como se ven las tablas
# =====================================
pd.set_option("display.max_columns", None)
pd.set_option("display.max_rows", 50)
pd.set_option("display.float_format", "{:.2f}".format)

print(f"Python executable: {sys.executable}")
print(f"Project root:      {PROJECT_ROOT}")
```

## Cell 2 - config-and-source-selection

**Explicacion:** 5. Cargar la configuracion del proyecto Esta configuracion ya conoce la liga, las temporadas y las rutas oficiales.

```python
# =========================================
# 5. Cargar la configuracion del proyecto
# =========================================
# Esta configuracion ya conoce la liga, las temporadas y las rutas oficiales.

config = load_ingestion_config()

INBOX_DIR = config.inbox_dir
RAW_DIR = config.raw_dir
SEASONS = config.seasons
LEAGUE = config.league

# ====================================================
# 6. Elegir desde donde queremos leer los archivos
# ====================================================
# Opciones:
# - "auto": si hay archivos manuales en `inbox`, usa esos; si no, usa `raw`
# - "inbox": fuerza la lectura de archivos manuales E0_<temporada>.csv
# - "raw": fuerza la lectura de archivos canonicos del pipeline

SOURCE_STAGE = "auto"

if SOURCE_STAGE not in {"auto", "inbox", "raw"}:
    raise ValueError("SOURCE_STAGE debe ser 'auto', 'inbox' o 'raw'.")

print(f"League:       {LEAGUE}")
print(f"Seasons:      {list(SEASONS)}")
print(f"Inbox dir:    {INBOX_DIR}")
print(f"Raw dir:      {RAW_DIR}")
print(f"Source mode:  {SOURCE_STAGE}")
```

## Cell 3 - build-file-map

**Explicacion:** 7. Construir las rutas esperadas para cada temporada `manual_files` apunta a los CSV descargados manualmente. `raw_files` apunta a los CSV canonicos del pipeline.

```python
# =====================================================
# 7. Construir las rutas esperadas para cada temporada
# =====================================================
# `manual_files` apunta a los CSV descargados manualmente.
# `raw_files` apunta a los CSV canonicos del pipeline.

manual_files = {}
raw_files = {}

for season in SEASONS:
    manual_files[season] = INBOX_DIR / config.manual_fallback_filename(season)
    raw_files[season] = config.canonical_csv_path(season)

# ======================================================
# 8. Resolver cual va a ser la fuente activa del notebook
# ======================================================
# Si SOURCE_STAGE = "auto", damos prioridad a `inbox` para empezar simple.

if SOURCE_STAGE == "auto":
    hay_archivos_manuales = any(path.exists() for path in manual_files.values())
    ACTIVE_STAGE = "inbox" if hay_archivos_manuales else "raw"
else:
    ACTIVE_STAGE = SOURCE_STAGE

if ACTIVE_STAGE == "inbox":
    FILE_MAP = manual_files
    SOURCE_DIR = INBOX_DIR
else:
    FILE_MAP = raw_files
    SOURCE_DIR = RAW_DIR

# ========================================================
# 9. Separar archivos disponibles y archivos faltantes
# ========================================================
available_files = {}
missing_files = {}

for season, csv_path in FILE_MAP.items():
    if csv_path.exists():
        available_files[season] = csv_path
    else:
        missing_files[season] = csv_path.name

print(f"Active stage:  {ACTIVE_STAGE}")
print(f"Using dir:     {SOURCE_DIR}")
print(f"Available:     {len(available_files)}")

if missing_files:
    print(f"Missing files: {missing_files}")

if not available_files:
    raise FileNotFoundError(
        "No se encontraron archivos locales. Coloca E0_<temporada>.csv en data/bronze/matchhistory/inbox o ejecuta .\\scripts\\refresh-matchhistory.ps1 para poblar data/bronze/matchhistory/raw."
    )
```

## Cell 4 - csv-reader-helper

**Explicacion:** 10. Crear un helper simple para leer los CSV Primero probamos `utf-8-sig` porque estos CSV pueden traer BOM. Si eso falla, intentamos con `latin-1`.

```python
# =============================================
# 10. Crear un helper simple para leer los CSV
# =============================================
# Primero probamos `utf-8-sig` porque estos CSV pueden traer BOM.
# Si eso falla, intentamos con `latin-1`.

def read_local_csv(csv_path: Path):
    last_error = None

    for encoding in ("utf-8-sig", "latin-1"):
        try:
            dataframe = pd.read_csv(csv_path, encoding=encoding)
            return dataframe, encoding
        except UnicodeDecodeError as exc:
            last_error = exc

    raise ValueError(
        f"No se pudo leer {csv_path.name} con utf-8-sig ni latin-1: {last_error}"
    )
```

## Cell 5 - load-loop

**Explicacion:** 11. Recorrer cada temporada y cargar los CSV disponibles Si falta algun archivo, lo informamos y seguimos con los demas.

```python
# ========================================================
# 11. Recorrer cada temporada y cargar los CSV disponibles
# ========================================================
# Si falta algun archivo, lo informamos y seguimos con los demas.

dataframes = []
loaded_seasons = []

for season in SEASONS:
    csv_path = FILE_MAP[season]

    if not csv_path.exists():
        print(f"FALTA  Temporada {season}: {csv_path.name}")
        continue

    df_season, encoding_used = read_local_csv(csv_path)

    # Agregamos columnas extra para saber de donde salio cada fila.
    df_season["season"] = season
    df_season["league"] = LEAGUE
    df_season["source_stage"] = ACTIVE_STAGE
    df_season["source_file"] = csv_path.name

    dataframes.append(df_season)
    loaded_seasons.append(season)

    print(
        f"OK  Temporada {season}: {len(df_season)} partidos | "
        f"archivo={csv_path.name} | encoding={encoding_used}"
    )
```

## Cell 6 - concat-and-summary

**Explicacion:** 12. Unir todas las temporadas en un solo DF `df_raw` va a ser la tabla base para explorar.

```python
# ============================================
# 12. Unir todas las temporadas en un solo DF
# ============================================
# `df_raw` va a ser la tabla base para explorar.

if not dataframes:
    raise FileNotFoundError(
        "No hay archivos disponibles en el stage seleccionado. Revisa inbox/raw y vuelve a ejecutar."
    )

df_raw = pd.concat(dataframes, ignore_index=True)

print(f"Total partidos cargados: {len(df_raw)}")
print(f"Columnas:                {df_raw.shape[1]}")
print(f"Temporadas cargadas:     {loaded_seasons}")

display(df_raw.head())
display(df_raw.groupby(["season", "source_stage"]).size().rename("matches").to_frame())
```

## Cell 7 - basic-audit

**Explicacion:** 13. Auditoria basica del dataset Revisamos columnas, tipos, nulos y cantidad de partidos por temporada.

```python
# ==================================
# 13. Auditoria basica del dataset
# ==================================
# Revisamos columnas, tipos, nulos y cantidad de partidos por temporada.

print("Columnas:")
display(pd.DataFrame({"column": df_raw.columns}))

print("Tipos:")
display(df_raw.dtypes.rename("dtype").to_frame())

print("Nulos por columna:")
display(df_raw.isna().sum().rename("nulls").sort_values(ascending=False).to_frame())

print("Conteo por temporada:")
display(df_raw["season"].value_counts().sort_index().rename("matches").to_frame())
```
