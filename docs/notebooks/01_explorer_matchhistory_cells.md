# Codigo de Celdas del Notebook: 01_explorer_matchhistory.ipynb

> Archivo generado automaticamente desde `notebooks/01_explorer_matchhistory.ipynb`.
> Regenerar con `.\scripts\export-notebook-cells.ps1` cuando cambie el notebook fuente.

<!-- notebook-source: notebooks/01_explorer_matchhistory.ipynb -->
<!-- notebook-code-and-outputs-sha256: 1160356eeb03da8ff3aa261fecf25ba9ef5896b5a2fa85f5fe41a965118a32a6 -->

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

**Output 1:**

```text
Python executable: c:\Users\Asus\Desktop\football-ml\.venv\Scripts\python.exe
Project root:      c:\Users\Asus\Desktop\football-ml
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

**Output 1:**

```text
League:       ENG-Premier League
Seasons:      ['2122', '2223', '2324']
Inbox dir:    C:\Users\Asus\Desktop\football-ml\data\bronze\matchhistory\inbox
Raw dir:      C:\Users\Asus\Desktop\football-ml\data\bronze\matchhistory\raw
Source mode:  auto
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

**Output 1:**

```text
Active stage:  inbox
Using dir:     C:\Users\Asus\Desktop\football-ml\data\bronze\matchhistory\inbox
Available:     3
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

**Output:** Sin output guardado en el notebook.

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

**Output 1:**

```text
OK  Temporada 2122: 380 partidos | archivo=E0_2122.csv | encoding=utf-8-sig
OK  Temporada 2223: 380 partidos | archivo=E0_2223.csv | encoding=utf-8-sig
OK  Temporada 2324: 380 partidos | archivo=E0_2324.csv | encoding=utf-8-sig
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

**Output 1:**

```text
Total partidos cargados: 1140
Columnas:                110
Temporadas cargadas:     ['2122', '2223', '2324']
```

**Output 2:**

```text
  Div        Date   Time    HomeTeam        AwayTeam  FTHG  FTAG FTR  HTHG  \
0  E0  13/08/2021  20:00   Brentford         Arsenal     2     0   H     1   
1  E0  14/08/2021  12:30  Man United           Leeds     5     1   H     1   
2  E0  14/08/2021  15:00     Burnley        Brighton     1     2   A     1   
3  E0  14/08/2021  15:00     Chelsea  Crystal Palace     3     0   H     2   
4  E0  14/08/2021  15:00     Everton     Southampton     3     1   H     0   

   HTAG HTR    Referee  HS  AS  HST  AST  HF  AF  HC  AC  HY  AY  HR  AR  \
0     0   H   M Oliver   8  22    3    4  12   8   2   5   0   0   0   0   
1     0   H  P Tierney  16  10    8    3  11   9   5   4   1   2   0   0   
2     0   H    D Coote  14  14    3    8  10   7   7   6   2   1   0   0   
3     0   H     J Moss  13   4    6    1  15  11   5   2   0   0   0   0   
4     1   A   A Madley  14   6    6    3  13  15   6   8   2   0   0   0   

   B365H  B365D  B365A  BWH  BWD   BWA  IWH  IWD   IWA  PSH  PSD   PSA  WHH  \
0   4.00   3.40   1.95 4.00 3.50  1.95 3.80 3.40  2.05 4.05 3.46  2.05 4.00   
1   1.53   4.50   5.75 1.53 4.50  5.75 1.55 4.40  5.75 1.56 4.57  5.96 1.52   
2   3.10   3.10   2.45 3.20 3.10  2.40 3.15 3.05  2.45 3.30 3.12  2.51 3.20   
3   1.25   5.75  13.00 1.28 5.75 10.50 1.25 6.00 13.00 1.26 6.24 12.74 1.25   
4   1.90   3.50   4.00 1.95 3.50  3.90 1.95 3.45  3.95 2.01 3.56  4.10 1.95   

   WHD   WHA  VCH  VCD   VCA  MaxH  MaxD  MaxA  AvgH  AvgD  AvgA  B365>2.5  \
0 3.40  1.90 4.10 3.40  2.00  4.62  3.72  2.10  4.02  3.43  2.02      2.10   
1 4.33  5.80 1.55 4.40  6.00  1.59  4.65  6.35  1.55  4.48  5.87      1.61   
2 3.00  2.45 3.13 3.10  2.45  3.33  3.20  2.60  3.19  3.09  2.49      2.50   
3 5.50 13.00 1.25 5.75 13.00  1.30  6.30 15.00  1.26  5.92 12.80      1.80   
4 3.40  4.00 1.95 3.40  4.10  2.04  3.66  4.25  1.97  3.53  4.04      2.00   

   B365<2.5  P>2.5  P<2.5  Max>2.5  Max<2.5  Avg>2.5  Avg<2.5   AHh  B365AHH  \
0      1.72   2.22   1.73     2.26     1.83     2.16     1.73  0.50     1.86   
1      2.30   1.67   2.32     1.71     2.38     1.65     2.29 -1.00     1.95   
2      1.53   2.56   1.56     2.56     1.63     2.46     1.57  0.25     1.80   
3      2.00   1.80   2.09     1.84     2.12     1.79     2.06 -1.50     1.84   
4      1.80   2.14   1.78     2.14     1.85     2.07     1.79 -0.50     2.00   

   B365AHA  PAHH  PAHA  MaxAHH  MaxAHA  AvgAHH  AvgAHA  B365CH  B365CD  \
0     2.07  1.88  2.06    2.05    2.08    1.87    2.03    3.80    3.25   
1     1.98  1.96  1.96    2.00    2.01    1.93    1.96    1.61    4.20   
2     2.14  1.83  2.12    1.83    2.17    1.79    2.12    3.10    3.10   
3     2.09  1.79  2.12    1.93    2.12    1.83    2.07    1.30    5.25   
4     1.93  2.01  1.92    2.01    1.97    1.96    1.92    2.00    3.40   

   B365CA  BWCH  BWCD  BWCA  IWCH  IWCD  IWCA  PSCH  PSCD  PSCA  WHCH  WHCD  \
0    2.05  3.80  3.30  2.05  3.80  3.25  2.10  3.94  3.33  2.13  3.90  3.00   
1    5.25  1.62  4.10  5.25  1.65  4.20  4.90  1.67  4.20  5.40  1.57  4.20   
2    2.45  3.25  3.10  2.40  3.10  3.05  2.45  3.27  3.14  2.51  3.10  3.00   
3   11.00  1.33  5.00 10.00  1.30  5.25 11.00  1.34  5.40 11.00  1.30  5.25   
4    3.90  2.05  3.40  3.75  2.00  3.35  4.00  2.05  3.45  4.07  1.95  3.40   

   WHCA  VCCH  VCCD  VCCA  MaxCH  MaxCD  MaxCA  AvgCH  AvgCD  AvgCA  \
0  2.05  3.90  3.25  2.10   4.20   3.50   2.18   3.89   3.28   2.10   
1  5.50  1.65  4.10  5.25   1.71   4.33   5.80   1.64   4.19   5.22   
2  2.45  3.13  3.13  2.50   3.35   3.20   2.56   3.19   3.10   2.48   
3 10.00  1.33  5.00 11.00   1.36   5.50  11.50   1.33   5.17  10.58   
4  3.90  2.00  3.30  4.20   2.12   3.50   4.20   2.04   3.39   3.95   

   B365C>2.5  B365C<2.5  PC>2.5  PC<2.5  MaxC>2.5  MaxC<2.5  AvgC>2.5  \
0       2.37       1.57    2.44    1.62      2.47      1.75      2.33   
1       1.66       2.20    1.70    2.27      1.75      2.37      1.67   
2       2.30       1.61    2.33    1.67      2.42      1.71      2.34   
3       1.90       1.90    1.93    1.98      1.96      2.07      1.90   
4       2.20       1.66    2.28    1.69      2.34      1.77      2.24   

   AvgC<2.5  AHCh  B365CAHH  B365CAHA  PCAHH  PCAHA  MaxCAHH  MaxCAHA  \
0      1.62  0.50      1.75      2.05   1.81   2.13     2.05     2.17   
1      2.25 -1.00      2.05      1.75   2.17   1.77     2.19     1.93   
2      1.62  0.25      1.79      2.15   1.81   2.14     1.82     2.19   
3      1.94 -1.50      2.05      1.75   2.12   1.81     2.16     1.93   
4      1.67 -0.50      2.05      1.88   2.05   1.88     2.08     1.90   

   AvgCAHH  AvgCAHA season              league source_stage  source_file  
0     1.80     2.09   2122  ENG-Premier League        inbox  E0_2122.csv  
1     2.10     1.79   2122  ENG-Premier League        inbox  E0_2122.csv  
2     1.79     2.12   2122  ENG-Premier League        inbox  E0_2122.csv  
3     2.06     1.82   2122  ENG-Premier League        inbox  E0_2122.csv  
4     2.03     1.86   2122  ENG-Premier League        inbox  E0_2122.csv
```

**Output 3:**

```text
                     matches
season source_stage         
2122   inbox             380
2223   inbox             380
2324   inbox             380
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

**Output 1:**

```text
Columnas:
```

**Output 2:**

```text
           column
0             Div
1            Date
2            Time
3        HomeTeam
4        AwayTeam
..            ...
105       AvgCAHA
106        season
107        league
108  source_stage
109   source_file

[110 rows x 1 columns]
```

**Output 3:**

```text
Tipos:
```

**Output 4:**

```text
                dtype
Div            object
Date           object
Time           object
HomeTeam       object
AwayTeam       object
...               ...
AvgCAHA       float64
season         object
league         object
source_stage   object
source_file    object

[110 rows x 1 columns]
```

**Output 5:**

```text
Nulos por columna:
```

**Output 6:**

```text
             nulls
IWCA           185
IWCD           185
IWCH           185
IWH            182
IWA            182
...            ...
WHH              0
PSA              0
PSD              0
PSH              0
source_file      0

[110 rows x 1 columns]
```

**Output 7:**

```text
Conteo por temporada:
```

**Output 8:**

```text
        matches
season         
2122        380
2223        380
2324        380
```
