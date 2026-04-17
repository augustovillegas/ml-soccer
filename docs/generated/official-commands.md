# Comandos Oficiales

> Archivo generado automaticamente desde `config/project_governance.toml`.

## Registro

## 01 - `bootstrap_project`

- Script: `scripts/bootstrap.ps1`
- Comando base: `.\scripts\bootstrap.ps1`
- Objetivo: Preparar el entorno gobernado, instalar dependencias, registrar kernel y dejar hooks/configuracion base listas.
- Verificacion minima: El script termina sin errores y la validacion estructural final pasa.
- Visible en bitacora: `true`

- Artefacto impactado: `.venv`
- Artefacto impactado: `.githooks`
- Artefacto impactado: `logs/governance/command-ledger.jsonl`

## 02 - `validate_project`

- Script: `scripts/validate-project.ps1`
- Comando base: `.\scripts\validate-project.ps1`
- Objetivo: Validar contratos, notebooks, documentacion generada, reglas de drift y consistencia estructural del proyecto.
- Verificacion minima: La salida contiene 'Project validation passed.' para el scope ejecutado.
- Visible en bitacora: `true`

- Artefacto impactado: `logs/governance/command-ledger.jsonl`

## 03 - `sync_project`

- Script: `scripts/sync-project.ps1`
- Comando base: `.\scripts\sync-project.ps1`
- Objetivo: Resincronizar artefactos generados, respaldos de notebooks, bitacora y dependencias derivadas.
- Verificacion minima: La salida confirma que los artefactos gobernados quedaron sincronizados.
- Visible en bitacora: `true`

- Artefacto impactado: `BITACORA_ENTORNO.md`
- Artefacto impactado: `docs/generated/README.md`
- Artefacto impactado: `docs/generated/official-commands.md`
- Artefacto impactado: `docs/generated/project-status.md`
- Artefacto impactado: `docs/notebooks/README.md`
- Artefacto impactado: `docs/notebooks/*_cells.md`
- Artefacto impactado: `requirements.txt`
- Artefacto impactado: `logs/governance/command-ledger.jsonl`

## 04 - `scaffold_notebook`

- Script: `scripts/scaffold-notebook.ps1`
- Comando base: `.\scripts\scaffold-notebook.ps1`
- Objetivo: Crear un notebook oficial nuevo, registrarlo en el manifiesto y regenerar sus artefactos gobernados.
- Verificacion minima: El notebook nuevo queda registrado en config/project_governance.toml y sus docs generadas existen.
- Visible en bitacora: `true`

- Artefacto impactado: `config/project_governance.toml`
- Artefacto impactado: `notebooks`
- Artefacto impactado: `docs/notebooks`
- Artefacto impactado: `docs/generated`
- Artefacto impactado: `BITACORA_ENTORNO.md`
- Artefacto impactado: `logs/governance/command-ledger.jsonl`

## 05 - `export_notebook_cells`

- Script: `scripts/export-notebook-cells.ps1`
- Comando base: `.\scripts\export-notebook-cells.ps1`
- Objetivo: Regenerar los exports Markdown de notebooks oficiales a partir de sus celdas y outputs guardados.
- Verificacion minima: Cada docs/notebooks/*_cells.md queda alineado con su notebook fuente.
- Visible en bitacora: `true`

- Artefacto impactado: `docs/notebooks/*_cells.md`
- Artefacto impactado: `logs/governance/command-ledger.jsonl`

## 06 - `ingest_matchhistory`

- Script: `scripts/ingest-matchhistory.ps1`
- Comando base: `.\scripts\ingest-matchhistory.ps1`
- Objetivo: Actualizar la ingesta bronze de MatchHistory con descarga automatica, fallback manual y manifests por temporada.
- Verificacion minima: La salida termina en 'Ingestion completed.' y los manifests quedan actualizados.
- Visible en bitacora: `true`

- Artefacto impactado: `data/bronze/matchhistory/raw`
- Artefacto impactado: `data/bronze/matchhistory/manifests`
- Artefacto impactado: `docs/generated/project-status.md`
- Artefacto impactado: `BITACORA_ENTORNO.md`
- Artefacto impactado: `logs/governance/command-ledger.jsonl`

## 07 - `refresh_matchhistory`

- Script: `scripts/refresh-matchhistory.ps1`
- Comando base: `.\scripts\refresh-matchhistory.ps1`
- Objetivo: Ejecutar la validacion runtime y luego refrescar MatchHistory mediante el workflow oficial diario.
- Verificacion minima: La validacion runtime pasa y la ingesta concluye sin errores.
- Visible en bitacora: `true`

- Artefacto impactado: `data/bronze/matchhistory/raw`
- Artefacto impactado: `data/bronze/matchhistory/manifests`
- Artefacto impactado: `docs/generated/project-status.md`
- Artefacto impactado: `BITACORA_ENTORNO.md`
- Artefacto impactado: `logs/governance/command-ledger.jsonl`

## 08 - `watch_project`

- Script: `scripts/watch-project.ps1`
- Comando base: `.\scripts\watch-project.ps1`
- Objetivo: Levantar el watcher local para resincronizar artefactos gobernados casi en tiempo real.
- Verificacion minima: La consola informa que el watcher esta activo y resincroniza cambios detectados.
- Visible en bitacora: `true`

- Artefacto impactado: `docs/generated`
- Artefacto impactado: `docs/notebooks`
- Artefacto impactado: `requirements.txt`
- Artefacto impactado: `BITACORA_ENTORNO.md`
- Artefacto impactado: `logs/governance/command-ledger.jsonl`
