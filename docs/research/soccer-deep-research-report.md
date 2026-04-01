# Soccerdata para machine learning en fútbol

## Resumen ejecutivo

`soccerdata` es una librería de Python orientada a extraer y normalizar datos de fútbol desde múltiples fuentes, con salida principal en `pandas.DataFrame` y soporte de caché local. Para este proyecto, su valor principal está en facilitar una primera capa de ingestión y exploración para tareas de análisis y modelado.

En la versión `1.8.8`, la API pública expone scrapers para:

- `ClubElo`
- `ESPN`
- `FBref`
- `MatchHistory`
- `Sofascore`
- `SoFIFA`
- `Understat`
- `WhoScored`

Para objetivos de machine learning sobre resultados y eventos de partidos, las fuentes más relevantes son:

- `MatchHistory`: resultados históricos, odds y estadísticas de partido
- `Understat`: xG, tiros y métricas avanzadas
- `FBref`: estadísticas agregadas, fixtures y eventos
- `ClubElo`: ratings históricos de equipos
- `WhoScored`: flujo de eventos detallado

## Puntos clave para este proyecto

### 1. MatchHistory es útil para una capa bronze inicial

`MatchHistory` es una de las fuentes más directas para comenzar un pipeline de datos de partidos porque entrega:

- goles finales y al descanso
- resultado del partido
- árbitro
- tiros y tiros al arco
- fouls, córners y tarjetas
- múltiples columnas de odds

Método principal:

```python
mh = sd.MatchHistory(leagues="ENG-Premier League", seasons=["2122", "2223", "2324"])
df = mh.read_games()
```

### 2. Los identificadores de liga deben usar el formato interno de soccerdata

Para Premier League, el identificador esperado es:

```python
"ENG-Premier League"
```

Esto es importante porque la librería usa claves internas por país y competencia.

### 3. Las temporadas deben declararse en un formato no ambiguo

En este proyecto conviene usar:

```python
["2122", "2223", "2324"]
```

Evitar valores como `2021`, `2022` o `2023` cuando la fuente o el scraper puedan interpretarlos de forma ambigua.

### 4. El caché y los datos raw deben quedar dentro del proyecto

Aunque `soccerdata` puede guardar caché en una ruta de usuario global, para este proyecto conviene usar `data_dir` dentro de `data/bronze/...` para mantener una estructura reproducible.

Ejemplo:

```python
from pathlib import Path

RUTA_BRONZE = Path("data/bronze/matchhistory")

mh = sd.MatchHistory(
    leagues="ENG-Premier League",
    seasons=["2122", "2223", "2324"],
    data_dir=RUTA_BRONZE,
)
```

## Riesgos operativos

### 1. Fragilidad del scraping

La librería depende de sitios externos que pueden cambiar HTML, endpoints o medidas anti-bot. Eso significa que una configuración correcta localmente no garantiza disponibilidad permanente de la fuente.

### 2. Indisponibilidad temporal del proveedor

En `MatchHistory`, la descarga depende de `football-data.co.uk`. Si el sitio devuelve `HTTP 503`, el problema debe tratarse primero como indisponibilidad del proveedor externo y no como falla del entorno local, del kernel o de las dependencias instaladas.

### 3. Diferencias entre documentación, metadata y estado real

En librerías de scraping es común que la documentación, PyPI y el código no estén siempre alineados al cien por ciento. Por eso, antes de asumir soporte de una fuente, conviene validar:

- clases realmente expuestas por la versión instalada
- métodos disponibles
- estabilidad real de la fuente

## API pública relevante

### Clases principales expuestas

- `ClubElo`
- `ESPN`
- `FBref`
- `MatchHistory`
- `Sofascore`
- `SoFIFA`
- `Understat`
- `WhoScored`

### Métodos útiles para pipelines

- `MatchHistory.read_games()`
- `FBref.read_schedule()`
- `FBref.read_team_match_stats()`
- `FBref.read_shot_events()`
- `Understat.read_team_match_stats()`
- `Understat.read_shot_events()`
- `WhoScored.read_events()`
- `ClubElo.read_by_date()`

## Recomendaciones para implementación

### Estructura de datos

- `data/bronze`: datos raw descargados desde la fuente
- `data/silver`: normalización y limpieza
- `data/gold`: datasets listos para análisis o modelado

### Convención para notebooks

- usar kernel dedicado del proyecto
- validar `sys.executable` al inicio
- parametrizar `league`, `seasons` y `data_dir`
- capturar errores de red con `try/except`

### Convención para validación inicial

Después de descargar datos, revisar al menos:

- `shape`
- columnas
- tipos de dato
- nulos por columna
- rango temporal

## Recomendación práctica para este proyecto

La secuencia más razonable para empezar es:

1. Descargar `MatchHistory` para Premier League en `bronze`
2. Explorar columnas, tipos y nulos
3. Definir un contrato mínimo de datos para partidos
4. Evaluar luego joins con `Understat`, `FBref` o `ClubElo`

## Fuentes de referencia recomendadas

- Documentación oficial: `https://soccerdata.readthedocs.io/en/latest/`
- Referencia de API: `https://soccerdata.readthedocs.io/en/latest/reference/index.html`
- Repositorio: `https://github.com/probberechts/soccerdata`
- PyPI: `https://pypi.org/project/soccerdata/`

## Uso de este documento

Este archivo debe utilizarse como referencia interna primaria del proyecto cada vez que haya que profundizar sobre:

- qué fuentes soporta `soccerdata`
- cómo configurar `MatchHistory`
- qué riesgos tiene el scraping
- cómo integrar la librería dentro de notebooks y pipelines del proyecto
