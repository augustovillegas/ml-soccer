# Soccerdata para machine learning en futbol

## Resumen ejecutivo

`soccerdata` es una libreria de Python para extraer y normalizar datos de futbol desde varias fuentes publicas. En este proyecto sirve como puerta de entrada rapida para construir una capa `bronze` reproducible y explorarla con `pandas`.

La version instalada en el proyecto es `1.8.8`. Las clases principales expuestas por la API incluyen:

- `ClubElo`
- `ESPN`
- `FBref`
- `MatchHistory`
- `Sofascore`
- `SoFIFA`
- `Understat`
- `WhoScored`

## Fuentes mas utiles para este proyecto

- `MatchHistory`: resultados historicos, odds prepartido y estadisticas basicas de partido.
- `Understat`: xG, tiros y metricas avanzadas.
- `FBref`: estadisticas agregadas, fixtures y tablas.
- `ClubElo`: ratings historicos de equipos.
- `WhoScored`: eventos de partido mas detallados.

## MatchHistory como base bronze

`MatchHistory` es la fuente mas directa para iniciar un pipeline de partidos porque trabaja sobre los CSV de `football-data.co.uk` y ofrece un acceso simple por liga y temporada.

Ejemplo base:

```python
import soccerdata as sd

mh = sd.MatchHistory(
    leagues="ENG-Premier League",
    seasons=["2122", "2223", "2324"],
)
df = mh.read_games()
```

### Datos que normalmente aporta

- fecha del partido
- equipo local y visitante
- goles finales y al descanso
- resultado final
- arbitro
- tiros, tiros al arco, corners, fouls y tarjetas
- multiples columnas de odds

## Convenciones recomendadas en este proyecto

### Liga

Para Premier League, usar siempre:

```python
"ENG-Premier League"
```

### Temporadas

Usar temporadas no ambiguas:

```python
["2122", "2223", "2324"]
```

Evitar `2021`, `2022` o `2023` cuando la fuente pueda interpretarlas de manera ambigua.

### data_dir del proyecto

No depender del cache global del usuario. La configuracion del proyecto debe apuntar a una ruta dentro de `data/bronze/...`.

Ejemplo:

```python
from pathlib import Path

RUTA_BRONZE = Path("data/bronze/matchhistory/raw")

mh = sd.MatchHistory(
    leagues="ENG-Premier League",
    seasons=["2122", "2223", "2324"],
    data_dir=RUTA_BRONZE,
)
```

## Riesgos operativos

### Fragilidad del scraping

La libreria depende de sitios externos. Si cambian endpoints, HTML, protecciones anti-bot o disponibilidad, la configuracion local puede seguir correcta y aun asi fallar la descarga.

### Proveedor temporalmente caido

En `MatchHistory`, un `HTTP 503` desde `football-data.co.uk` debe tratarse primero como una indisponibilidad del proveedor externo y no como una falla de sintaxis, kernel o dependencias.

### Diferencia entre notebook e ingesta oficial

Los notebooks no deben ser la capa oficial de ingesta. La descarga y la validacion deben ejecutarse desde scripts o modulos reutilizables, y los notebooks deben leer CSV ya persistidos en `data/bronze`.

## Recomendacion operativa

Para este proyecto, la estrategia mas estable es:

1. Intentar descarga automatica con `soccerdata`.
2. Guardar CSV canonicos en `data/bronze/matchhistory/raw`.
3. Si el proveedor responde `503`, usar fallback manual con CSV en `data/bronze/matchhistory/inbox`.
4. Explorar datos desde bronze en Jupyter, sin volver a descargar desde la red.

Esa separacion reduce friccion, mejora la reproducibilidad y deja la automatizacion lista para conectarse mas adelante a un scheduler.
