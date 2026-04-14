# Como Continuar el ETL de MatchHistory

## Resumen

Este documento resume el estado actual del proyecto y explica como seguir sin mezclar aprendizaje, exploracion y pipeline productivo.

La recomendacion actual es:

- usar el notebook como laboratorio de transformacion
- no volver a mover la extraccion al notebook
- construir primero una capa `silver` minima y consistente
- no mezclar de entrada temporadas cerradas con la temporada en curso `2025/2026`

Fecha de referencia de esta guia: **2 de abril de 2026**.

## Que ya esta resuelto

Hoy el proyecto ya tiene estas piezas estables:

- entorno reproducible en Windows con `.venv`
- kernel dedicado `football-ml (.venv)` para Jupyter
- estructura `data/bronze`, `data/silver`, `data/gold`, `models`, `notebooks`
- ingesta oficial fuera del notebook
- refresh automatizado de `MatchHistory`
- fallback manual con archivos `E0_<temporada>.csv` en `data/bronze/matchhistory/inbox`
- notebook `01` de exploracion que lee datos locales y no descarga desde internet
- notebook `02` de transformacion `silver` que parte del Bronze local ya persistido
- documentacion exportada de los notebooks oficiales con codigo y outputs

En el estado actual, el notebook trabaja sobre datos locales y ya mostro:

- `1140` partidos
- `110` columnas
- `3` temporadas completas: `2122`, `2223`, `2324`

Eso significa que la capa `bronze` inicial ya existe y ya sirve como base para explorar.

Ademas, el repositorio ya distribuye para revision completa los artefactos oficiales persistidos de MatchHistory:

- CSV canonicos en `data/bronze/matchhistory/raw`
- manifests JSON en `data/bronze/matchhistory/manifests`
- `data/bronze/matchhistory/raw/matches_bronze.parquet`
- `data/silver/matches_silver.parquet`

Siguen fuera de Git:

- `data/bronze/matchhistory/inbox` como staging manual transitorio
- `logs/`
- caches, checkpoints y el entorno `.venv`

## Que significa cada capa en este proyecto

### Extraccion

La extraccion ya no depende del notebook.

Se resuelve por:

- scripts oficiales del proyecto
- o fallback manual con CSV descargados desde `football-data.co.uk`

### Bronze

`bronze` es el dato crudo persistido.

Es la capa donde guardas:

- archivos descargados manualmente en `inbox`
- archivos canonicos del pipeline en `raw`
- manifests de ingesta en `manifests`

### Notebook

Los notebooks oficiales no son la ingesta oficial.

Su funcion correcta es:

- `01`: cargar CSV locales, auditar el dataset y cerrar Bronze
- `02`: leer el parquet Bronze local, derivar columnas para modelado y cerrar Silver
- mantener un formato comun de bootstrap, encabezados numerados e IDs de celdas estables

### Silver

`silver` deberia ser la primera tabla limpia y consistente reutilizable del proyecto.

No es todavia la etapa de features finales ni de modelado.

## Por que el siguiente paso es ETL exploratorio en notebook

Todavia no conviene pasar directo a un script definitivo de transformacion.

Primero hace falta responder preguntas basicas:

- que columnas se quedan
- cuales se descartan
- cuales tienen problemas de tipos
- cuales tienen nulos
- cuales son consistentes entre temporadas
- cual va a ser la definicion minima de tu tabla limpia

Por eso el siguiente paso correcto es un **ETL exploratorio dentro del notebook**, no un ETL productivo cerrado.

## Secuencia recomendada de trabajo

### 1. Perfilar el bronze

Primero separa mentalmente tres grupos de columnas:

- identidad del partido
- resultado y estadisticas del partido
- odds

No intentes decidir sobre las 110 columnas todas juntas.

### 2. Definir una silver minima

Para una V1, la recomendacion es quedarse con una tabla simple:

- `Date`
- `HomeTeam`
- `AwayTeam`
- `FTHG`
- `FTAG`
- `FTR`
- `HTHG`
- `HTAG`
- `HTR`
- `HS`
- `AS`
- `HST`
- `AST`
- `HC`
- `AC`
- `HY`
- `AY`
- `HR`
- `AR`
- `Referee`
- `season`
- `league`
- `source_file`

Esa version ya alcanza para entender el dataset y tener una base util para seguir.

### 3. Hacer normalizacion basica

Lo primero que deberias estandarizar es:

- `Date` a fecha real con `dayfirst=True`
- tipos numericos en columnas de goles y estadisticas
- validacion de nulos en columnas clave

Columnas donde no deberias aceptar nulos sin revisar:

- `Date`
- `HomeTeam`
- `AwayTeam`
- `FTHG`
- `FTAG`
- `FTR`
- `season`

No conviene hacer un renombrado masivo si todavia estas entendiendo el dataset.

### 4. Validar reglas logicas del partido

Antes de guardar una primera `silver`, revisa:

- que `FTR` coincida con `FTHG` y `FTAG`
- que `HST <= HS`
- que `AST <= AS`
- que no haya duplicados por `Date + HomeTeam + AwayTeam + season`
- que cada temporada cerrada este cerca de `380` partidos

### 5. Recién despues pensar en guardar silver

La pregunta correcta todavia no es:

- "como modelo esto"

La pregunta correcta es:

- "que tabla limpia quiero dejar como base estable"

Cuando esa respuesta ya sea consistente, recien ahi conviene mover la logica a script o modulo y guardar en `data/silver`.

## Cosas que conviene evitar

### No mezclar aprendizaje con produccion

La regla recomendada es:

- en notebook prototipas
- en script consolidas

### No arrancar con todas las columnas de odds

Primero defini una `silver` robusta con variables de partido.

Despues, si realmente hace falta, armas:

- una silver de odds
- o una seleccion reducida de odds utiles

### No usar informacion post-partido como feature pre-partido

Mas adelante, si haces modelado, hay riesgo de leakage.

Por ejemplo:

- `FTHG`
- `FTAG`
- `FTR`

pueden ser labels o targets, pero no features para predecir ese mismo partido antes de que ocurra.

## Que temporadas existen y cuales conviene usar ahora

Segun la pagina oficial de Inglaterra de `football-data.co.uk`, al **2 de abril de 2026** estan listadas, entre otras:

- `2025/2026`
- `2024/2025`
- `2023/2024`
- `2022/2023`
- `2021/2022`

y muchas temporadas anteriores.

Para Premier League, la fuente oficial muestra:

- cobertura rica con resultados, match stats y odds desde `2000/2001`
- temporadas aun mas antiguas con resultados historicos y menor nivel de detalle

### Recomendacion practica

No arrancar con todo el historial.

Secuencia recomendada:

1. trabajar con `2122`, `2223`, `2324`
2. despues agregar `2425`
3. evaluar `2526` por separado

### Por que separar `2526`

La temporada `2025/2026` esta en curso al **2 de abril de 2026**.

Eso implica:

- incompletitud natural
- potenciales diferencias de cobertura
- riesgo de mezclar partidos cerrados con una temporada viva

Por eso, para aprender ETL y definir `silver`, es mejor empezar con temporadas cerradas.

## Criterio para salir del notebook

Podes pasar del notebook a script cuando se cumplan estas condiciones:

- ya sabes que columnas entran y cuales no
- la fecha esta bien parseada
- no hay duplicados inesperados
- `FTR` coincide con los goles
- la tabla `silver` es consistente por temporada
- podes rerunear la misma logica sobre otra temporada sin romper nada

## Camino recomendado desde hoy

### Etapa 1

- trabajar con `2122`, `2223`, `2324`
- terminar una `silver` minima y limpia

### Etapa 2

- agregar `2425`
- verificar que la transformacion siga funcionando

### Etapa 3

- evaluar `2526` aparte
- tratarla como temporada en curso, no como base inicial de entrenamiento

### Etapa 4

- cuando la transformacion del notebook ya sea estable, moverla a script o modulo
- recien ahi guardar en `data/silver`

## Regla operativa para notebooks futuros

Tomar `notebooks/01_explorer_matchhistory.ipynb` como referencia estructural para cualquier notebook oficial nuevo.

Eso implica:

- nombre `NN_<etapa>_<tema>.ipynb`
- kernel `football-ml (.venv)`
- primera celda con bootstrap comun del proyecto
- celdas con encabezados numerados y comentario explicativo
- IDs de celda descriptivos y estables
- export obligatorio a `docs/notebooks/..._cells.md`
- si cambia codigo u output guardado del notebook, el export Markdown debe regenerarse
- validacion final con `.\scripts\validate-project.ps1 -Scope project`

## Nota de escalado

- Mientras `silver` siga exploratoria, `notebooks/02_silver_matchhistory.ipynb` puede seguir escribiendo `data/silver/matches_silver.parquet`.
- Ese archivo en la raiz de `data/silver` se considera una excepcion transitoria documentada.
- Cuando aparezca un segundo dataset `silver` oficial o un segundo consumidor de la transformacion, la ownership debe migrar a `src/football_ml/` + `scripts/*` y los datasets nuevos deben ir bajo un namespace de dominio.
- La referencia operativa para estas reglas es [reglas-escalado-seguro.md](./reglas-escalado-seguro.md).

## Nota sobre odds recientes

La fuente oficial de `football-data.co.uk` advierte que desde el **23 de julio de 2025** la API publica de Pinnacle se volvio poco confiable.

Eso no invalida `MatchHistory`, pero si obliga a tratar con mas cuidado cualquier analisis que dependa especificamente de esas odds.

## Fuentes y documentos de apoyo

- Referencia interna principal sobre `soccerdata`: [../research/soccer-deep-research-report.md](../research/soccer-deep-research-report.md)
- Estado operativo del proyecto: [../../BITACORA_ENTORNO.md](../../BITACORA_ENTORNO.md)
- Notebook `01` de referencia: [../../notebooks/01_explorer_matchhistory.ipynb](../../notebooks/01_explorer_matchhistory.ipynb)
- Export `01`: [../notebooks/01_explorer_matchhistory_cells.md](../notebooks/01_explorer_matchhistory_cells.md)
- Notebook `02` oficial: [../../notebooks/02_silver_matchhistory.ipynb](../../notebooks/02_silver_matchhistory.ipynb)
- Export `02`: [../notebooks/02_silver_matchhistory_cells.md](../notebooks/02_silver_matchhistory_cells.md)
- Documentacion oficial de `MatchHistory`: [soccerdata MatchHistory](https://soccerdata.readthedocs.io/en/stable/reference/matchhistory.html)
- Cobertura general de la fuente: [football-data main page](https://www.football-data.co.uk/data.php)
- Cobertura oficial de Inglaterra al 2 de abril de 2026: [football-data England page](https://www.football-data.co.uk/englandm.php)
