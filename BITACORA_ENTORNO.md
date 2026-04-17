# Bitacora de entorno y comandos

> Archivo generado automaticamente desde `config/project_governance.toml`.

## Criterio operativo

- La receta oficial del proyecto vive en `config/project_governance.toml`.
- Esta bitacora lista solo comandos oficiales gobernados por scripts del repositorio.
- Las ejecuciones reales se registran en `logs/governance/command-ledger.jsonl`.
- Los comandos directos fuera de los scripts oficiales no forman parte de esta bitacora automatica.

## Receta oficial

### 1. `bootstrap_project`

Comando base:

```powershell
.\scripts\bootstrap.ps1
```

Objetivo: Preparar el entorno gobernado, instalar dependencias, registrar kernel y dejar hooks/configuracion base listas.

Verificacion minima:

- El script termina sin errores y la validacion estructural final pasa.

Artefactos impactados:

- `.venv`
- `.githooks`
- `logs/governance/command-ledger.jsonl`

Evidencia auditada: consultar `logs/governance/command-ledger.jsonl` para `bootstrap_project`.

### 2. `validate_project`

Comando base:

```powershell
.\scripts\validate-project.ps1
```

Objetivo: Validar contratos, notebooks, documentacion generada, reglas de drift y consistencia estructural del proyecto.

Verificacion minima:

- La salida contiene 'Project validation passed.' para el scope ejecutado.

Artefactos impactados:

- `logs/governance/command-ledger.jsonl`

Evidencia auditada: consultar `logs/governance/command-ledger.jsonl` para `validate_project`.

### 3. `sync_project`

Comando base:

```powershell
.\scripts\sync-project.ps1
```

Objetivo: Resincronizar artefactos generados, respaldos de notebooks, bitacora y dependencias derivadas.

Verificacion minima:

- La salida confirma que los artefactos gobernados quedaron sincronizados.

Artefactos impactados:

- `BITACORA_ENTORNO.md`
- `docs/generated/README.md`
- `docs/generated/official-commands.md`
- `docs/generated/project-status.md`
- `docs/notebooks/README.md`
- `docs/notebooks/*_cells.md`
- `requirements.txt`
- `logs/governance/command-ledger.jsonl`

Evidencia auditada: consultar `logs/governance/command-ledger.jsonl` para `sync_project`.

### 4. `scaffold_notebook`

Comando base:

```powershell
.\scripts\scaffold-notebook.ps1
```

Objetivo: Crear un notebook oficial nuevo, registrarlo en el manifiesto y regenerar sus artefactos gobernados.

Verificacion minima:

- El notebook nuevo queda registrado en config/project_governance.toml y sus docs generadas existen.

Artefactos impactados:

- `config/project_governance.toml`
- `notebooks`
- `docs/notebooks`
- `docs/generated`
- `BITACORA_ENTORNO.md`
- `logs/governance/command-ledger.jsonl`

Evidencia auditada: consultar `logs/governance/command-ledger.jsonl` para `scaffold_notebook`.

### 5. `export_notebook_cells`

Comando base:

```powershell
.\scripts\export-notebook-cells.ps1
```

Objetivo: Regenerar los exports Markdown de notebooks oficiales a partir de sus celdas y outputs guardados.

Verificacion minima:

- Cada docs/notebooks/*_cells.md queda alineado con su notebook fuente.

Artefactos impactados:

- `docs/notebooks/*_cells.md`
- `logs/governance/command-ledger.jsonl`

Evidencia auditada: consultar `logs/governance/command-ledger.jsonl` para `export_notebook_cells`.

### 6. `ingest_matchhistory`

Comando base:

```powershell
.\scripts\ingest-matchhistory.ps1
```

Objetivo: Actualizar la ingesta bronze de MatchHistory con descarga automatica, fallback manual y manifests por temporada.

Verificacion minima:

- La salida termina en 'Ingestion completed.' y los manifests quedan actualizados.

Artefactos impactados:

- `data/bronze/matchhistory/raw`
- `data/bronze/matchhistory/manifests`
- `docs/generated/project-status.md`
- `BITACORA_ENTORNO.md`
- `logs/governance/command-ledger.jsonl`

Evidencia auditada: consultar `logs/governance/command-ledger.jsonl` para `ingest_matchhistory`.

### 7. `refresh_matchhistory`

Comando base:

```powershell
.\scripts\refresh-matchhistory.ps1
```

Objetivo: Ejecutar la validacion runtime y luego refrescar MatchHistory mediante el workflow oficial diario.

Verificacion minima:

- La validacion runtime pasa y la ingesta concluye sin errores.

Artefactos impactados:

- `data/bronze/matchhistory/raw`
- `data/bronze/matchhistory/manifests`
- `docs/generated/project-status.md`
- `BITACORA_ENTORNO.md`
- `logs/governance/command-ledger.jsonl`

Evidencia auditada: consultar `logs/governance/command-ledger.jsonl` para `refresh_matchhistory`.

### 8. `watch_project`

Comando base:

```powershell
.\scripts\watch-project.ps1
```

Objetivo: Levantar el watcher local para resincronizar artefactos gobernados casi en tiempo real.

Verificacion minima:

- La consola informa que el watcher esta activo y resincroniza cambios detectados.

Artefactos impactados:

- `docs/generated`
- `docs/notebooks`
- `requirements.txt`
- `BITACORA_ENTORNO.md`
- `logs/governance/command-ledger.jsonl`

Evidencia auditada: consultar `logs/governance/command-ledger.jsonl` para `watch_project`.
