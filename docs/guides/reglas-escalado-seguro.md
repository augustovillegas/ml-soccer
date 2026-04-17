# Reglas de escalado seguro para football-ml

## 1. Fuente oficial por clase

- `config/project_governance.toml` gobierna notebooks oficiales, watcher, comandos oficiales y documentos generados.
- `config/ingestion.toml` gobierna MatchHistory y su operacion oficial.
- `src/football_ml/*` + `scripts/*` son la implementacion oficial.
- `docs/generated/*`, `docs/notebooks/*` y `BITACORA_ENTORNO.md` son salidas generadas.
- `docs/guides/*` solo guarda criterio durable; no debe repetir metricas, schedules, proximos notebooks ni comandos internos derivados.
- `docs/research/*` concentra investigacion y soporte tecnico.

## 2. Activos generados vs manuales

- Los generados no se editan manualmente; se corrigen modificando su fuente y ejecutando `.\scripts\sync-project.ps1` o dejando actuar al watcher.
- Si una fuente oficial cambia, el cambio no esta cerrado hasta que todos los derivados queden sincronizados.
- Los notebooks oficiales solo pueden leer datos locales y deben conservar bootstrap comun, IDs estables y export a `docs/notebooks/*`.
- Los datasets oficiales viven con contrato en codigo. Los nuevos `silver` y `gold` van bajo namespace de dominio.
- `data/silver/matches_silver.parquet` sigue siendo una excepcion transitoria mientras `silver` permanezca exploratoria.

## 3. Operacion oficial

- Toda operacion auditada debe pasar por scripts oficiales gobernados.
- El watcher local `.\scripts\watch-project.ps1` es el mecanismo primario de resincronizacion casi en tiempo real.
- Los hooks locales y CI actuan como respaldo; no reemplazan al watcher.
- La ingesta online pertenece a scripts/modulos de `bronze`, no a notebooks.
- Cuando una transformacion `silver` tenga segundo consumidor o automatizacion, migra a `src/football_ml/` + `scripts/*`.

## 4. Cierre de cambio

- `.\scripts\sync-project.ps1` es el gate de sincronizacion de artefactos derivados.
- `.\scripts\validate-project.ps1 -Scope project` es el gate estructural.
- `.\.venv\Scripts\python.exe -m pytest` es el gate funcional offline.
- Si alguno de esos pasos detecta drift, el cambio sigue abierto.

## 5. Anti-mojibake

- Todo cierre incluye revision anti-mojibake sobre los archivos fuente modificados.
- Si hay texto mal decodificado visible, el cambio no se considera terminado.
