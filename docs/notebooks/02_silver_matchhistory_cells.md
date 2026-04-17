# Codigo de Celdas del Notebook: 02_silver_matchhistory.ipynb

> Archivo generado automaticamente desde `notebooks/02_silver_matchhistory.ipynb`.
> Regenerar con `.\scripts\export-notebook-cells.ps1` cuando cambie el notebook fuente.

<!-- notebook-source: notebooks/02_silver_matchhistory.ipynb -->
<!-- notebook-code-and-outputs-sha256: 733d7b2fbba7d38e644b4966b52cd550cba231dc3bfac155e86bd9777d63a03c -->

## Cell 1 - imports-and-kernel-check

**Explicacion:** 1. Importar librerias basicas `sys` nos permite ver que Python esta usando el notebook. `Path` sirve para manejar rutas de archivos de forma clara. `pandas` es la libreria principal para leer el parquet Bronze.

```python
# ==============================
# 1. Importar librerias basicas
# ==============================
# `sys` nos permite ver que Python esta usando el notebook.
# `Path` sirve para manejar rutas de archivos de forma clara.
# `pandas` es la libreria principal para leer el parquet Bronze.

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
# 3. Ajustar como se ven las tablas en pantalla
# =============================================
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

## Cell 2 - bronze-parquet-load

**Explicacion:** 4. Cargar el parquet Bronze del proyecto Este notebook parte desde el Bronze persistido por el notebook 01.

```python
# =========================================
# 4. Cargar el parquet Bronze del proyecto
# =========================================
# Este notebook parte desde el Bronze persistido por el notebook 01.

RUTA_BRONZE = PROJECT_ROOT / "data" / "bronze" / "matchhistory" / "raw" / "matches_bronze.parquet"

if not RUTA_BRONZE.exists():
    raise FileNotFoundError(
        "No se encontro el Bronze local. Ejecuta primero el notebook 01 hasta guardar matches_bronze.parquet."
    )

df = pd.read_parquet(RUTA_BRONZE)

print(f"Partidos cargados: {len(df)}")
print(f"Columnas:          {df.shape[1]}")
print(f"Fechas:            {df['Date'].min().date()} -> {df['Date'].max().date()}")
print(f"Tipo Date:         {df['Date'].dtype}")
display(df.head(3))
```

**Output 1:**

```text
Partidos cargados: 1140
Columnas:          27
Fechas:            2021-08-13 -> 2024-05-19
Tipo Date:         datetime64[ns]
```

**Output 2:**

```text
        Date    HomeTeam  AwayTeam season              league FTR  FTHG  FTAG  \
0 2021-08-13   Brentford   Arsenal   2122  ENG-Premier League   H     2     0   
1 2021-08-14  Man United     Leeds   2122  ENG-Premier League   H     5     1   
2 2021-08-14     Burnley  Brighton   2122  ENG-Premier League   A     1     2   

   HTHG  HTAG HTR  HS  AS  HST  AST  HF  AF  HY  AY  HR  AR  B365H  B365D  \
0     1     0   H   8  22    3    4  12   8   0   0   0   0   4.00   3.40   
1     1     0   H  16  10    8    3  11   9   1   2   0   0   1.53   4.50   
2     1     0   H  14  14    3    8  10   7   2   1   0   0   3.10   3.10   

   B365A  PSH  PSD  PSA  
0   1.95 4.05 3.46 2.05  
1   5.75 1.56 4.57 5.96  
2   2.45 3.30 3.12 2.51
```

## Cell 3 - game-key-derivation

**Explicacion:** 5. Construir una clave unica por partido `game_key` nos sirve para cruzar este dataset con otras fuentes despues.

```python
# ===========================================
# 5. Construir una clave unica por partido
# ===========================================
# `game_key` nos sirve para cruzar este dataset con otras fuentes despues.

df["game_key"] = (
    df["Date"].dt.strftime("%Y-%m-%d")
    + " "
    + df["HomeTeam"]
    + "-"
    + df["AwayTeam"]
)

duplicados = df["game_key"].duplicated().sum()

print(f"Partidos duplicados por game_key: {duplicados}")
display(df[["Date", "HomeTeam", "AwayTeam", "game_key"]].head(5))
```

**Output 1:**

```text
Partidos duplicados por game_key: 0
```

**Output 2:**

```text
        Date    HomeTeam        AwayTeam                           game_key
0 2021-08-13   Brentford         Arsenal       2021-08-13 Brentford-Arsenal
1 2021-08-14  Man United           Leeds        2021-08-14 Man United-Leeds
2 2021-08-14     Burnley        Brighton        2021-08-14 Burnley-Brighton
3 2021-08-14     Chelsea  Crystal Palace  2021-08-14 Chelsea-Crystal Palace
4 2021-08-14     Everton     Southampton     2021-08-14 Everton-Southampton
```

## Cell 4 - bet365-probability-normalization

**Explicacion:** 6. Normalizar las odds 1X2 de Bet365 a probabilidades Primero calculamos probabilidades brutas y despues removemos el overround.

```python
# ====================================================
# 6. Normalizar las odds 1X2 de Bet365 a probabilidades
# ====================================================
# Primero calculamos probabilidades brutas y despues removemos el overround.

df["prob_bruta_H"] = 1 / df["B365H"]
df["prob_bruta_D"] = 1 / df["B365D"]
df["prob_bruta_A"] = 1 / df["B365A"]
df["overround"] = df["prob_bruta_H"] + df["prob_bruta_D"] + df["prob_bruta_A"]

df["prob_H"] = df["prob_bruta_H"] / df["overround"]
df["prob_D"] = df["prob_bruta_D"] / df["overround"]
df["prob_A"] = df["prob_bruta_A"] / df["overround"]

# Limpiamos las columnas intermedias para dejar solo el resultado util.
df = df.drop(columns=["prob_bruta_H", "prob_bruta_D", "prob_bruta_A"])

print(f"Overround promedio Bet365: {(df['overround'] - 1).mean():.2%}")
print(
    f"Suma probabilidad 1X2 (debe dar 1.0): {(df['prob_H'] + df['prob_D'] + df['prob_A']).round(4).unique()}"
)
display(
    df[["HomeTeam", "AwayTeam", "B365H", "B365D", "B365A", "overround", "prob_H", "prob_D", "prob_A"]].head(5)
)
```

**Output 1:**

```text
Overround promedio Bet365: 5.39%
Suma probabilidad 1X2 (debe dar 1.0): [1.]
```

**Output 2:**

```text
     HomeTeam        AwayTeam  B365H  B365D  B365A  overround  prob_H  prob_D  \
0   Brentford         Arsenal   4.00   3.40   1.95       1.06    0.24    0.28   
1  Man United           Leeds   1.53   4.50   5.75       1.05    0.62    0.21   
2     Burnley        Brighton   3.10   3.10   2.45       1.05    0.31    0.31   
3     Chelsea  Crystal Palace   1.25   5.75  13.00       1.05    0.76    0.17   
4     Everton     Southampton   1.90   3.50   4.00       1.06    0.50    0.27   

   prob_A  
0    0.49  
1    0.17  
2    0.39  
3    0.07  
4    0.24
```

## Cell 5 - target-encoding

**Explicacion:** 7. Codificar el target del partido `FTR` esta como texto y lo convertimos a una clase numerica.

```python
# =====================================
# 7. Codificar el target del partido
# =====================================
# `FTR` esta como texto y lo convertimos a una clase numerica.

df["target"] = df["FTR"].map({"H": 0, "D": 1, "A": 2})

conteo = df["target"].value_counts().sort_index()
conteo.index = ["0=Local gana", "1=Empate", "2=Visita gana"]
pct = (conteo / len(df) * 100).round(1)

print("Distribucion del target:")
for nombre, n, p in zip(conteo.index, conteo.values, pct.values):
    print(f"  {nombre}: {n} partidos ({p}%)")
```

**Output 1:**

```text
Distribucion del target:
  0=Local gana: 522 partidos (45.8%)
  1=Empate: 257 partidos (22.5%)
  2=Visita gana: 361 partidos (31.7%)
```

## Cell 6 - silver-build-and-write

**Explicacion:** 8. Construir y guardar la tabla Silver Seleccionamos las columnas finales y persistimos un parquet reutilizable.

```python
# =====================================
# 8. Construir y guardar la tabla Silver
# =====================================
# Seleccionamos las columnas finales y persistimos un parquet reutilizable.

COLS_SILVER = [
    "game_key", "Date", "season", "league", "HomeTeam", "AwayTeam",
    "FTR", "target",
    "FTHG", "FTAG",
    "HS", "AS", "HST", "AST", "HF", "AF", "HY", "AY",
    "prob_H", "prob_D", "prob_A", "overround",
    "B365H", "B365D", "B365A",
]

df_silver = df[COLS_SILVER].copy()

RUTA_SILVER = PROJECT_ROOT / "data" / "silver"
RUTA_SILVER.mkdir(parents=True, exist_ok=True)

ruta_silver = RUTA_SILVER / "matches_silver.parquet"
df_silver.to_parquet(ruta_silver, index=False, compression="snappy")

kb = ruta_silver.stat().st_size / 1024
print(f"Silver guardado en: {ruta_silver}")
print(f"Tamano:            {kb:.1f} KB")
print(f"Filas:             {len(df_silver)}")
print(f"Columnas:          {df_silver.shape[1]}")
display(df_silver.head(3))
```

**Output 1:**

```text
Silver guardado en: c:\Users\Asus\Desktop\football-ml\data\silver\matches_silver.parquet
Tamano:            67.9 KB
Filas:             1140
Columnas:          25
```

**Output 2:**

```text
                       game_key       Date season              league  \
0  2021-08-13 Brentford-Arsenal 2021-08-13   2122  ENG-Premier League   
1   2021-08-14 Man United-Leeds 2021-08-14   2122  ENG-Premier League   
2   2021-08-14 Burnley-Brighton 2021-08-14   2122  ENG-Premier League   

     HomeTeam  AwayTeam FTR  target  FTHG  FTAG  HS  AS  HST  AST  HF  AF  HY  \
0   Brentford   Arsenal   H       0     2     0   8  22    3    4  12   8   0   
1  Man United     Leeds   H       0     5     1  16  10    8    3  11   9   1   
2     Burnley  Brighton   A       2     1     2  14  14    3    8  10   7   2   

   AY  prob_H  prob_D  prob_A  overround  B365H  B365D  B365A  
0   0    0.24    0.28    0.49       1.06   4.00   3.40   1.95  
1   2    0.62    0.21    0.17       1.05   1.53   4.50   5.75  
2   1    0.31    0.31    0.39       1.05   3.10   3.10   2.45
```

## Cell 7 - silver-summary

**Explicacion:** 9. Cerrar Silver y resumir el estado Dejamos visible que genero este notebook y cual es el siguiente paso.

```python
# =====================================
# 9. Cerrar Silver y resumir el estado
# =====================================
# Dejamos visible que genero este notebook y cual es el siguiente paso.

print("=" * 45)
print("RESUMEN - Notebook 02: Silver ETL")
print("=" * 45)
print()
print(f"Partidos procesados: {len(df_silver)}")
print(f"Temporadas:          {sorted(df_silver['season'].unique())}")
print(f"Rango de fechas:     {df_silver['Date'].min().date()} -> {df_silver['Date'].max().date()}")
print()
print("Columnas Silver:")
for column in df_silver.columns:
    print(f"  {column}")
print()
print("Notebook 02 completo.")
print("Siguiente: consolidar Silver en codigo cuando deje de ser exploratoria")
```

**Output 1:**

```text
=============================================
RESUMEN - Notebook 02: Silver ETL
=============================================

Partidos procesados: 1140
Temporadas:          ['2122', '2223', '2324']
Rango de fechas:     2021-08-13 -> 2024-05-19

Columnas Silver:
  game_key
  Date
  season
  league
  HomeTeam
  AwayTeam
  FTR
  target
  FTHG
  FTAG
  HS
  AS
  HST
  AST
  HF
  AF
  HY
  AY
  prob_H
  prob_D
  prob_A
  overround
  B365H
  B365D
  B365A

Notebook 02 completo.
Siguiente: consolidar Silver en codigo cuando deje de ser exploratoria
```
