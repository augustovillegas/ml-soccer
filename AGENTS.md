# Reglas operativas para agentes

## 1. Fuente oficial por clase de activo

- `config/project_governance.toml` gobierna entorno, watcher, comandos oficiales, documentos generados y notebooks oficiales.
- `config/ingestion.toml` gobierna MatchHistory, su automatizacion y sus rutas oficiales.
- `src/football_ml/*` y `scripts/*` son la implementacion oficial.
- `pyproject.toml` es la fuente primaria de dependencias directas; `requirements.txt` es su artefacto sincronizado.
- `docs/generated/*`, `docs/notebooks/*` y `BITACORA_ENTORNO.md` son documentos generados. No se editan manualmente.
- `docs/guides/*` contiene criterio durable y continuidad operativa. No puede repetir estado vivo derivable.
- `docs/research/*` contiene investigacion y referencia tecnica. Para `soccerdata`, la referencia interna primaria es `docs/research/soccer-deep-research-report.md`.

## 2. Activos generados vs manuales

- Si un cambio toca una fuente oficial, el watcher o `.\scripts\sync-project.ps1` debe dejar todos los derivados sincronizados.
- Si despues del cambio quedan artefactos generados desalineados, el cambio esta incompleto.
- `bronze` pertenece a scripts y modulos de ingesta, no a notebooks.
- `silver` puede seguir owned por notebook solo mientras sea exploratoria y tenga un solo consumidor.
- `gold` no debe nacer en notebook.
- Todo dataset oficial debe existir en codigo con nombre canonico, stage, path, columnas minimas, clave de unicidad y politica de actualizacion.
- Los datasets nuevos en `data/silver` y `data/gold` deben ir namespaced por dominio. `data/silver/matches_silver.parquet` sigue siendo una excepcion transitoria documentada.
- Los artefactos generados locales como `*.egg-info/`, `.ipynb_checkpoints`, `.pytest_cache` y temporales no deben quedar versionados.

## 3. Operacion oficial

- En Windows usar siempre `.\.venv\Scripts\python.exe` y `.\.venv\Scripts\python.exe -m pip ...`.
- Los comandos oficiales del proyecto son `.\scripts\bootstrap.ps1`, `.\scripts\validate-project.ps1`, `.\scripts\sync-project.ps1`, `.\scripts\watch-project.ps1`, `.\scripts\scaffold-notebook.ps1`, `.\scripts\export-notebook-cells.ps1`, `.\scripts\ingest-matchhistory.ps1` y `.\scripts\refresh-matchhistory.ps1`.
- Toda operacion que deba quedar documentada o auditada debe ejecutarse por esos scripts o por wrappers gobernados del repositorio.
- Los notebooks oficiales deben estar registrados en `config/project_governance.toml`, usar el kernel `football-ml (.venv)`, bootstrap comun, IDs estables y solo leer datos locales.
- Toda automatizacion oficial ejecuta scripts, no notebooks, y debe dejar evidencia en manifests o logs locales.
- En flujos con `soccerdata`, usar `data_dir` dentro de `data/bronze/...`.
- Si `MatchHistory` devuelve `HTTP 503` o `ConnectionError`, tratarlo primero como indisponibilidad temporal del proveedor.
- Si falla la descarga automatica, el fallback manual usa `data/bronze/matchhistory/inbox` con nombres exactos `E0_<temporada>.csv`.

## 4. Cierre de cambio

- Ejecutar `.\scripts\sync-project.ps1` cuando cambie una fuente gobernada o cualquier artefacto derivable.
- Ejecutar `.\scripts\validate-project.ps1 -Scope project` como gate estructural del proyecto.
- Ejecutar `.\.venv\Scripts\python.exe -m pytest` como gate funcional offline.
- Si cambian dependencias directas, actualizar primero `pyproject.toml` y despues resincronizar `requirements.txt`.
- Si cambia un notebook oficial, el cierre requiere sync, validacion estructural y regeneracion de `docs/notebooks/*`.
- No cerrar un cambio con secciones impactadas desalineadas respecto del estado real del proyecto.

## 5. Regla anti-mojibake

- Antes de cerrar cualquier cambio, verificar que los archivos fuente modificados no tengan mojibake visible.
- Esta regla aplica aunque el cambio no sea documental y aunque no involucre notebooks.
- La verificacion anti-mojibake forma parte obligatoria del cierre junto con sync, validacion y tests.
