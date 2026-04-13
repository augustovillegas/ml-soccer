# Reglas de Escalado Seguro para football-ml

## Resumen

Estas reglas fijan como escalar el proyecto sin perder eficiencia operativa ni introducir drift entre codigo, datos, notebooks y documentacion.

La idea central es simple:

- una fuente oficial por tipo de activo
- un owner claro por dataset y por capa
- contratos minimos de dataset validados en codigo
- tests offline baratos antes de sumar complejidad

## Fuente oficial por tipo de activo

- `AGENTS.md` define reglas operativas obligatorias.
- `BITACORA_ENTORNO.md` registra comandos, cambios operativos y verificaciones reproducibles.
- `docs/guides/*` explica como operar, continuar o escalar.
- `docs/notebooks/*` solo replica notebooks oficiales.
- `src/football_ml/*` y `scripts/*` son la implementacion oficial.

Si una regla o un flujo aparece en dos lugares, uno debe quedar como fuente primaria y el otro debe referenciarlo, no reescribirlo con variaciones.

## Ownership por capa

- `bronze`: la ingesta online y el refresh pertenecen a `src/football_ml/ingest` + `scripts/*`.
- `silver`: mientras siga exploratoria y con un solo consumidor, el notebook oficial puede escribir el artefacto canonico.
- `gold`: no debe nacer en notebook; cuando aparezca, debe nacer con script owner y contrato de dataset.

Regla de migracion:

- si una transformacion tiene segundo consumidor, automatizacion o reutilizacion fuera del notebook, deja de ser ownership del notebook y migra a codigo versionado en `src/football_ml/` + `scripts/*`.

## Contratos minimos de dataset

Todo dataset oficial debe registrarse en codigo con:

- `dataset_id`
- `stage`
- `domain`
- `path` oficial
- columnas minimas requeridas
- clave de unicidad
- politica de actualizacion

La validacion del proyecto debe revisar esos contratos contra el archivo real cuando el dataset ya existe localmente.

## Estructura escalable de datos

- No versionar outputs de `data/` ni de `logs/`, salvo `*.gitkeep`.
- Los datasets nuevos en `silver` y `gold` no deben vivir como archivos sueltos en la raiz del stage.
- Los datasets nuevos deben ir namespaced por dominio, por ejemplo `data/silver/matchhistory/...`.

Excepcion transitoria actual:

- `data/silver/matches_silver.parquet` sigue permitido como excepcion documentada mientras `silver` continue exploratoria y no exista un segundo dataset `silver` oficial.

## Notebooks oficiales

- Solo son oficiales los notebooks registrados en `src/football_ml/paths.py`.
- Todo notebook oficial nuevo requiere, en el mismo cambio:
  - alta en el registro oficial
  - export a `docs/notebooks/..._cells.md`
  - validacion estructural
  - actualizacion de la guia operativa impactada
- Los notebooks oficiales no son duenios de ingesta online.
- Los `.ipynb_checkpoints` no deben quedar versionados.

## Configuracion y parametrizacion

- Los paths oficiales, temporadas, nombres de tareas y valores operativos variables viven en config o en registros oficiales de codigo.
- No hardcodear nuevos paths oficiales dentro de notebooks.
- Si aparece un segundo workflow o dataset, separar su config en nuevas secciones o archivos antes de repetir claves ambiguas.

## Cierre de cambio

Cada cambio debe revisar su impacto en:

- codigo fuente
- config
- notebook oficial
- export Markdown
- guia operativa
- bitacora
- validacion
- tests

Si una de esas secciones cambia de hecho y no se actualiza, el cambio queda incompleto.

El chequeo anti-mojibake es obligatorio en cada cambio.

## Testing para escalar

Mantener dos niveles:

- tests rapidos de contrato y utilidades
- smoke tests offline contra datos locales ya persistidos

Cobertura minima actual recomendada:

- carga de config
- registro de notebooks oficiales
- contratos de datasets oficiales
- lectura CSV con fallback de encoding
- manifests Bronze
- fallback manual y caso provider unavailable
- desalineacion notebook/export Markdown
- artefactos generados trackeados por error

No agregar tests que requieran internet para el camino normal del proyecto.

## Automatizacion y observabilidad

- Toda automatizacion oficial ejecuta scripts, no notebooks.
- Toda automatizacion debe leer config oficial.
- Toda automatizacion debe dejar log local y evidencia minima de estado o manifest.
- Una sola tarea programada oficial por workflow.
- Cuando el volumen de logs crezca, definir retencion local antes de sumar nuevas automatizaciones.
