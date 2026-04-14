# Bitacora de entorno y comandos

Este documento registra, en orden cronologico y metodologico, los comandos correctos que funcionaron para dejar listo este proyecto en Windows PowerShell.

## Criterio operativo

- Usar siempre el interprete del entorno virtual de forma explicita: `.\.venv\Scripts\python.exe`.
- Evitar `pip` global. Ejecutar `python -m pip` contra el `python.exe` del entorno.
- Registrar solo la receta final que funciono. Los comandos incorrectos se anotan como correccion, no como paso recomendado.

## Paso a paso desde la creacion del entorno

### 1. Crear el entorno virtual de Windows

Comando:

```powershell
py -3.13 -m venv .venv
```

Resultado esperado:

- Se crea `.\.venv\Scripts\Activate.ps1`
- Se crea `.\.venv\Scripts\python.exe`

### 2. Activar el entorno en PowerShell

Comando:

```powershell
.\.venv\Scripts\Activate.ps1
```

Si PowerShell bloquea scripts en la sesion actual, usar primero:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\.venv\Scripts\Activate.ps1
```

Resultado esperado:

- El prompt puede mostrar `(.venv)`
- `python` pasa a resolver al ejecutable dentro de `.\.venv`

### 3. Verificar el interprete del entorno

Comando:

```powershell
.\.venv\Scripts\python.exe -V
```

Resultado observado:

```text
Python 3.13.3
```

### 4. Actualizar pip dentro del entorno

Comando:

```powershell
.\.venv\Scripts\python.exe -m pip install --upgrade pip
```

Resultado observado:

```text
Successfully installed pip-26.0.1
```

### 5. Instalar dependencias del proyecto

Comando correcto:

```powershell
.\.venv\Scripts\python.exe -m pip install soccerdata==1.8.8 pandas pyarrow jupyter notebook
```

Correccion aplicada:

- El nombre `jupyer` no existe en PyPI y falla con `No matching distribution found`.
- El nombre correcto del paquete es `jupyter`.

Paquetes principales instalados:

- `soccerdata==1.8.8`
- `pandas==2.3.3`
- `pyarrow==23.0.1`
- `jupyter==1.1.1`
- `notebook==7.5.5`

### 6. Verificar imports principales

Comando:

```powershell
.\.venv\Scripts\python.exe -c "import soccerdata, pandas, pyarrow, notebook; print('imports-ok')"
```

Resultado observado:

```text
imports-ok
```

Nota:

- `soccerdata` emitio mensajes informativos sobre archivos opcionales de configuracion del usuario, pero el import fue exitoso.

### 7. Verificar Jupyter Notebook

Comando:

```powershell
.\.venv\Scripts\python.exe -m jupyter --version
```

Resultado observado:

```text
IPython          : 9.12.0
ipykernel        : 7.2.0
ipywidgets       : 8.1.8
jupyter_client   : 8.8.0
jupyter_core     : 5.9.1
jupyter_server   : 2.17.0
jupyterlab       : 4.5.6
nbclient         : 0.10.4
nbconvert        : 7.17.0
nbformat         : 5.10.4
notebook         : 7.5.5
```

## Receta corta para repetir

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Estado final validado

- Entorno virtual Windows en `.\.venv`
- `pip` actualizado dentro del entorno
- Dependencias instaladas y verificadas
- `requirements.txt` creado para reproduccion del entorno

### 8. Crear estructura base de carpetas del proyecto

Comando:

```powershell
New-Item -ItemType Directory -Force -Path .\data\bronze, .\data\silver, .\data\gold, .\models, .\notebooks
```

Resultado observado:

- Se creo `data\bronze`
- Se creo `data\silver`
- Se creo `data\gold`
- Se creo `models`
- Se creo `notebooks`

### 9. Crear carpeta de documentacion tecnica y reubicar reporte de investigacion

Comando:

```powershell
New-Item -ItemType Directory -Force -Path .\docs\research
Move-Item -LiteralPath .\soccer-deep-research-report.md -Destination .\docs\research\soccer-deep-research-report.md
```

Resultado observado:

- Se creo `docs\research`
- El archivo `soccer-deep-research-report.md` quedo ubicado en `docs\research`

### 10. Registrar el reporte de soccerdata como documento obligatorio de consulta

Cambio aplicado:

- Se actualizo `AGENTS.md` para indicar que `docs\research\soccer-deep-research-report.md` debe consultarse primero cada vez que se necesite profundizar sobre la libreria `soccerdata`.

Resultado observado:

- El proyecto ya tiene una regla persistente para usar ese reporte como referencia interna primaria sobre `soccerdata`.

### 11. Registrar un kernel dedicado para el proyecto en Jupyter

Comando:

```powershell
.\.venv\Scripts\python.exe -m ipykernel install --prefix .\.venv --name football-ml --display-name "football-ml (.venv)"
```

Resultado observado:

- Se registro el kernel `football-ml`
- Jupyter dentro del entorno puede listar `football-ml (.venv)` como kernel dedicado del proyecto

### 12. Ajustar el notebook de MatchHistory para kernel y rutas del proyecto

Cambio aplicado:

- Se limpio `notebooks\01_explorer_matchhistory.ipynb`
- El notebook ahora usa el kernel `football-ml (.venv)`
- La primera celda imprime `sys.executable` para validar el interprete activo
- La segunda celda resuelve `RUTA_BRONZE` dentro de `data\bronze\matchhistory`
- La tercera celda usa `sd.MatchHistory(..., data_dir=RUTA_BRONZE)` y maneja errores de descarga con `try/except`

Resultado observado:

- La configuracion del notebook ya no depende del cache global de `C:\Users\Asus\soccerdata\data\MatchHistory`
- Si el proveedor `football-data.co.uk` responde `HTTP 503`, el error queda identificado como indisponibilidad externa y no como un problema local del entorno

### 13. Corregir mojibakes y fijar revision final obligatoria

Cambio aplicado:

- Se reemplazo `docs\research\soccer-deep-research-report.md` por una version limpia en UTF-8, sin mojibakes visibles ni artefactos de citacion corruptos.
- Se actualizaron las reglas en `AGENTS.md` para exigir una revision final anti-mojibake antes de cerrar cambios documentales o notebooks.

Procedimiento de revision final:

```powershell
.\scripts\validate-project.ps1
```

Resultado esperado:

- Validacion completa sin mojibakes en archivos fuente del proyecto

### 14. Crear la configuracion oficial de ingesta bronze

Cambio aplicado:

- Se agrego `config\ingestion.toml` como fuente unica de configuracion para `MatchHistory`.
- La configuracion fija la liga `ENG-Premier League`, las temporadas `2122`, `2223`, `2324`, el modo `hybrid` y las rutas oficiales `raw`, `inbox` y `manifests`.

Resultado observado:

- La automatizacion ya no depende de rutas hardcodeadas dispersas en notebooks.

### 15. Crear interfaces oficiales del proyecto

Comandos oficiales:

```powershell
.\scripts\bootstrap.ps1
.\scripts\validate-project.ps1
.\scripts\ingest-matchhistory.ps1
.\scripts\refresh-matchhistory.ps1
```

Resultado esperado:

- `bootstrap.ps1` prepara o valida el entorno, registra el kernel y corre la validacion final.
- `validate-project.ps1` revisa entorno, notebook, kernel, rutas y mojibake.
- `ingest-matchhistory.ps1` ejecuta el refresh de la ingesta bronze con fallback manual.
- `refresh-matchhistory.ps1` valida el runtime y ejecuta la actualizacion diaria de `MatchHistory`.

### 16. Ejecutar el refresh de la ingesta bronze con fallback manual

Comando:

```powershell
.\scripts\ingest-matchhistory.ps1
```

Comando para forzar una nueva ejecucion:

```powershell
.\scripts\ingest-matchhistory.ps1 -Force
```

Comando para limitar temporadas:

```powershell
.\scripts\ingest-matchhistory.ps1 -Seasons 2122,2223,2324
```

Resultado esperado:

- Si la descarga automatica funciona, se compara el checksum remoto contra el CSV canonico por temporada.
- Si cambia el contenido, se reemplaza `eng_premier_league_<temporada>.csv` en `data\bronze\matchhistory\raw`.
- Si el contenido no cambia, se registra `no_change_remote` y no se reescribe el archivo canonico.
- Si `football-data.co.uk` devuelve `503` o `ConnectionError`, la automatizacion busca CSV manuales canonicos en `data\bronze\matchhistory\inbox`.
- Si el proveedor falla y ya existe un CSV canonico valido, se registra `provider_unavailable_keep_current` y no se rompe el dataset actual.
- Cada temporada genera o actualiza un manifest JSON en `data\bronze\matchhistory\manifests` con `last_checked_at_utc`, `saved_at_utc`, `sha256` y `previous_sha256`.

### 17. Validar el proyecto despues de cambios estructurales

Comando:

```powershell
.\scripts\validate-project.ps1
```

Resultado esperado:

- `.gitignore` existe y protege entornos, checkpoints, logs y datos locales.
- Los notebooks oficiales usan el kernel `football-ml (.venv)` y no intentan scrapear datos online.
- Las rutas oficiales de `bronze` y `logs` existen.
- No quedan mojibakes visibles en archivos fuente controlados.

### 18. Registrar la tarea diaria de refresh

Comando:

```powershell
.\scripts\bootstrap.ps1
```

Comando efectivo usado internamente para registrar la tarea:

```powershell
schtasks /Create /SC DAILY /ST 09:00 /TN "football-ml-refresh-matchhistory" /TR "powershell.exe -NoProfile -ExecutionPolicy Bypass -File \"C:\Users\Asus\Desktop\football-ml\scripts\refresh-matchhistory.ps1\"" /F
```

Resultado esperado:

- `bootstrap.ps1` registra o actualiza la tarea programada `football-ml-refresh-matchhistory`.
- La tarea ejecuta diariamente `powershell.exe -NoProfile -ExecutionPolicy Bypass -File C:\Users\Asus\Desktop\football-ml\scripts\refresh-matchhistory.ps1`.
- La tarea no depende del directorio de trabajo porque `refresh-matchhistory.ps1` resuelve la raiz del proyecto desde su propia ruta.
- En esta maquina, la tarea quedo registrada bajo el usuario actual en modo interactivo.

### 19. Procedimiento manual de emergencia para CSV

Si la fuente remota no responde desde el script, descargar manualmente estos archivos, renombrarlos y colocarlos exactamente en `data\bronze\matchhistory\inbox`:

- `https://www.football-data.co.uk/mmz4281/2122/E0.csv` -> `E0_2122.csv`
- `https://www.football-data.co.uk/mmz4281/2223/E0.csv` -> `E0_2223.csv`
- `https://www.football-data.co.uk/mmz4281/2324/E0.csv` -> `E0_2324.csv`

Luego ejecutar:

```powershell
.\scripts\refresh-matchhistory.ps1
```

Resultado esperado:

- Si el CSV manual cambia respecto del canonico, el refresh reemplaza el archivo de `raw` y registra `updated_manual`.
- Si el contenido ya coincide, registra `no_change_manual`.

### 20. Instalar el paquete local en modo editable para resolver imports de `src`

Comando:

```powershell
.\.venv\Scripts\python.exe -m pip install -e .
```

Objetivo:

- Registrar `football_ml` como paquete editable dentro del `.venv` para que imports como `from football_ml.config import load_ingestion_config` funcionen sin depender de `PYTHONPATH`.

Verificacion minima:

```powershell
.\.venv\Scripts\python.exe -c "from football_ml.config import load_ingestion_config; print(load_ingestion_config().league)"
```

Resultado esperado:

- El import de `football_ml` resuelve correctamente desde el entorno virtual.
- El proyecto mantiene el layout `src/` sin romper scripts, notebooks ni analisis del editor.

Nota operativa:

- `bootstrap.ps1` instala automaticamente el paquete local en editable.
- El workspace tambien fija `.\.venv\Scripts\python.exe` y `src` en `.vscode\settings.json` para que el analizador del editor deje de marcar `football_ml` como no resuelto.

### 21. Adaptar el notebook de exploracion a un flujo simple y escalable

Cambio aplicado:

- Se rearmo `notebooks\01_explorer_matchhistory.ipynb` para trabajar en `dual mode`.
- El notebook ahora empieza por `data\bronze\matchhistory\inbox\E0_<temporada>.csv` cuando existen archivos manuales y escala a `data\bronze\matchhistory\raw\eng_premier_league_<temporada>.csv` cuando ya corre la automatizacion.
- La carga quedo separada en celdas progresivas: kernel, configuracion, seleccion de fuente, helper de lectura CSV, carga, resumen y auditoria basica.
- El notebook ya no descarga nada ni usa `soccerdata`; solo consume datos locales del proyecto.

Verificacion minima:

```powershell
.\scripts\validate-project.ps1 -Scope project
```

Resultado esperado:

- El notebook vuelve a usar el kernel `football-ml (.venv)`.
- La metadata ya no queda en `python3`.
- La exploracion inicial puede empezar desde `inbox` y luego pasar a `raw` sin cambiar la estructura del notebook.

### 22. Simplificar el notebook para un usuario principiante

Cambio aplicado:

- Se reescribio `notebooks\01_explorer_matchhistory.ipynb` con comentarios explicativos en cada bloque.
- Se usaron nombres de variables mas claros y una progresion simple: imports, configuracion, rutas, lectura, carga, resumen y auditoria.
- El notebook mantiene la logica `auto | inbox | raw`, pero con explicaciones pensadas para alguien que recien empieza.

Verificacion minima:

```powershell
.\scripts\validate-project.ps1 -Scope project
```

Resultado esperado:

- El notebook conserva el kernel `football-ml (.venv)`.
- Las celdas siguen siendo validas y el flujo de lectura local continua funcionando.

### 23. Exportar el codigo de las celdas del notebook a Markdown

Comando:

```powershell
.\scripts\export-notebook-cells.ps1
```

Objetivo:

- Generar `docs\notebooks\01_explorer_matchhistory_cells.md` a partir de `notebooks\01_explorer_matchhistory.ipynb`.
- Documentar el codigo de cada celda en orden, con una breve explicacion y los outputs textuales guardados del notebook, sin incluir metadata visual ni HTML crudo.

Verificacion minima:

```powershell
.\scripts\validate-project.ps1 -Scope project
```

Resultado esperado:

- Existe `docs\notebooks\01_explorer_matchhistory_cells.md`.
- El archivo incluye el codigo de cada celda en orden, sus outputs textuales y un marker interno con el notebook fuente.
- Si cambia el notebook y no se regenera el Markdown, `validate-project.ps1 -Scope project` falla por documento desactualizado.

### 24. Documentar como continuar el ETL sin mover la ingesta al notebook

Cambio aplicado:

- Se creo `docs\guides\como-continuar-etl.md` como guia manual de continuacion del proyecto.
- El documento resume que ya esta resuelto, que significa cada capa, por que el siguiente paso es ETL exploratorio en notebook y como pasar despues a `silver`.
- Tambien deja registrado que al 2 de abril de 2026 existen temporadas mas nuevas que `2122`, `2223` y `2324`, pero recomienda no empezar por la temporada en curso `2526`.

Verificacion minima:

```powershell
.\scripts\validate-project.ps1 -Scope project
```

Resultado esperado:

- La guia queda versionada dentro de `docs\guides`.
- El proyecto mantiene separadas las carpetas de research, notebooks generados y guias operativas.
- La documentacion queda alineada con el estado real del pipeline y con la fuente oficial consultada.

### 25. Crear el notebook `02_silver_matchhistory.ipynb` y sumarlo al flujo oficial

Comando:

```powershell
.\scripts\export-notebook-cells.ps1
```

Objetivo:

- Regenerar los respaldos Markdown oficiales de los notebooks gestionados por el proyecto.
- Confirmar que `docs\notebooks\01_explorer_matchhistory_cells.md` y `docs\notebooks\02_silver_matchhistory_cells.md` quedan sincronizados con sus notebooks fuente.

Verificacion minima:

```powershell
.\scripts\validate-project.ps1 -Scope project
```

Resultado esperado:

- Existe `notebooks\02_silver_matchhistory.ipynb`.
- El notebook usa el kernel `football-ml (.venv)` y reutiliza el mismo bootstrap comun de `01_explorer_matchhistory.ipynb`.
- Existe `docs\notebooks\02_silver_matchhistory_cells.md`.
- La validacion del proyecto revisa ambos notebooks oficiales y falla si alguno queda desactualizado respecto de su respaldo Markdown.

Receta manual reproducible:

```powershell
.\.venv\Scripts\python.exe -m notebook
```

1. Abrir Jupyter Notebook con el entorno del proyecto y seleccionar el kernel `football-ml (.venv)` para el archivo nuevo `notebooks\02_silver_matchhistory.ipynb`.
2. Copiar del notebook `01` solo el bootstrap comun: validacion del interprete, deteccion de `PROJECT_ROOT`, `EXPECTED_PYTHON`, chequeo del kernel y opciones de display.
3. Guardar el notebook nuevo sin mover la ingesta al notebook ni agregar llamadas online a `MatchHistory`; cada notebook mantiene la logica de su propia capa.
4. Ejecutar `.\scripts\export-notebook-cells.ps1` para generar o actualizar el respaldo `docs\notebooks\02_silver_matchhistory_cells.md`.
5. Ejecutar `.\scripts\validate-project.ps1 -Scope project` para comprobar kernel, sincronia de respaldos y revision anti-mojibake.

Nota de correccion:

- Antes el flujo oficial de exportacion y validacion estaba hardcodeado solo para `01_explorer_matchhistory.ipynb`; ahora contempla tambien `02_silver_matchhistory.ipynb` dentro de la lista oficial de notebooks gestionados.

### 26. Alinear el notebook `02` con el estandar de `01` y fijar reglas permanentes

Comandos:

```powershell
.\scripts\export-notebook-cells.ps1
.\scripts\validate-project.ps1 -Scope project
```

Objetivo:

- Reescribir `notebooks\02_silver_matchhistory.ipynb` con encabezados numerados estilo `01`, IDs de celdas estables y bootstrap comun del proyecto.
- Renombrar los IDs aleatorios pendientes de `notebooks\01_explorer_matchhistory.ipynb`.
- Dejar reglas persistentes en `AGENTS.md`, `docs\guides\como-continuar-etl.md` y `src\football_ml\validate.py` para que futuros notebooks oficiales sigan el mismo patron.

Verificacion minima:

```powershell
.\scripts\validate-project.ps1 -Scope project
```

Resultado esperado:

- `01_explorer_matchhistory.ipynb` y `02_silver_matchhistory.ipynb` usan IDs descriptivos y estables.
- `02_silver_matchhistory.ipynb` mantiene su logica Silver pero adopta el formato comun de `01`.
- `docs\notebooks\01_explorer_matchhistory_cells.md` y `docs\notebooks\02_silver_matchhistory_cells.md` quedan sincronizados.
- La validacion falla si un notebook oficial no respeta nombre, bootstrap, encabezados, IDs o sincronizacion con su Markdown exportado.

### 27. Saneamiento integral del repo y retiro de `egg-info` del versionado

Comandos:

```powershell
.\scripts\export-notebook-cells.ps1
.\scripts\validate-project.ps1 -Scope project
.\.venv\Scripts\python.exe -m pip install -e .
git rm -r --cached src\football_ml.egg-info
```

Objetivo:

- Resincronizar los respaldos Markdown oficiales con los outputs guardados reales de los notebooks.
- Ajustar la validacion y la documentacion para el flujo multi-notebook oficial.
- Dejar `src\football_ml.egg-info` como artefacto generado local y no como fuente versionada del proyecto.

Verificacion minima:

```powershell
.\scripts\validate-project.ps1 -Scope project
git status --short
```

Resultado esperado:

- `docs\notebooks\02_silver_matchhistory_cells.md` refleja el hash y los outputs actuales del notebook `02`.
- La validacion ignora `*.egg-info` como artefacto generado y sigue controlando notebooks, docs y codigo fuente.
- `git status --short` deja de mostrar `src\football_ml.egg-info\*` como parte del estado mantenido del repositorio.

### 28. Reforzar la regla de verificacion anti-mojibake como control general de cierre

Comando:

```powershell
.\scripts\validate-project.ps1 -Scope project
```

Objetivo:

- Dejar explicito en `AGENTS.md` que la revision anti-mojibake es obligatoria antes de cerrar cualquier tarea, no solo cambios documentales o de notebooks.

Verificacion minima:

```powershell
.\scripts\validate-project.ps1 -Scope project
```

Resultado esperado:

- `AGENTS.md` exige revisar mojibakes visibles en todos los archivos fuente modificados antes de cerrar una tarea.
- La regla aplica como control general de cierre del trabajo y no solo a documentacion o notebooks.

### 29. Personalizar la regla para que cada cambio actualice secciones impactadas y cierre con chequeo anti-mojibake

Comando:

```powershell
.\scripts\validate-project.ps1 -Scope project
```

Objetivo:

- Dejar explicito en `AGENTS.md` que cada cambio del proyecto debe mantener alineadas todas las secciones impactadas.
- Fijar que el chequeo anti-mojibake es obligatorio en cada cambio realizado y forma parte del cierre del trabajo.

Verificacion minima:

```powershell
.\scripts\validate-project.ps1 -Scope project
```

Resultado esperado:

- `AGENTS.md` obliga a actualizar codigo, notebooks, exports, guias, reglas y bitacora cuando el cambio los impacta.
- Ningun cambio se considera cerrado si alguna seccion afectada queda desalineada o si no se hizo la revision final anti-mojibake.

### 30. Agregar reglas de escalado seguro, contratos de dataset y tests offline

Comandos:

```powershell
.\scripts\validate-project.ps1 -Scope project
.\.venv\Scripts\python.exe -m pytest
git rm --cached notebooks\.ipynb_checkpoints\01_explorer_matchhistory-checkpoint.ipynb
```

Objetivo:

- Registrar reglas operativas de escalado en `AGENTS.md` y en `docs\guides\reglas-escalado-seguro.md`.
- Definir contratos minimos de datasets oficiales en `src\football_ml\paths.py`.
- Ampliar `src\football_ml\validate.py` para revisar contratos de dataset y artefactos generados versionados por error.
- Crear `tests\` con pruebas offline de contratos, utilidades y fallback de ingesta.
- Sacar del versionado el checkpoint trackeado del notebook.

Verificacion minima:

```powershell
.\scripts\validate-project.ps1 -Scope project
.\.venv\Scripts\python.exe -m pytest
git status --short
```

Resultado esperado:

- Existen contratos oficiales de dataset para Bronze y Silver.
- La validacion falla si reaparece un `.ipynb_checkpoints`, `*.egg-info`, `.pytest_cache`, datos versionados o logs versionados por error.
- `tests\` ejecuta pruebas offline y smoke tests locales sin depender de internet.
- El checkpoint `notebooks\.ipynb_checkpoints\01_explorer_matchhistory-checkpoint.ipynb` deja de formar parte del repositorio.

### 31. Publicar el repo con datos oficiales revisables y Git por SSH

Comando:

```powershell
git remote -v
```

Objetivo:

- Verificar el remoto oficial del repositorio antes de ajustar el versionado y el push.

Verificacion minima:

- `origin` apunta a `git@github.com:augustovillegas/ml-soccer.git` para fetch y push.

Comando:

```powershell
icacls $HOME\.ssh\id_ed25519 /inheritance:r
icacls $HOME\.ssh\id_ed25519 /grant:r "$((whoami)):(F)"
icacls $HOME\.ssh\id_ed25519 /grant:r "NT AUTHORITY\SYSTEM:(F)"
icacls $HOME\.ssh\id_ed25519 /grant:r "BUILTIN\Administradores:(F)"
```

Objetivo:

- Dejar la clave privada SSH con permisos compatibles con OpenSSH en Windows para que Git pueda intentar autenticarse contra GitHub.

Verificacion minima:

```powershell
icacls $HOME\.ssh\id_ed25519
```

Resultado esperado:

- La ACL de `id_ed25519` queda limitada al usuario actual, `SYSTEM` y `Administradores`.
- Desaparece el error de permisos abiertos sobre la clave privada.

Correccion relevante:

- Antes de fijar la ACL correcta, OpenSSH rechazaba `id_ed25519` por permisos demasiado amplios.

Comando:

```powershell
git config core.sshCommand "ssh -i C:/Users/Asus/.ssh/id_ed25519 -o IdentitiesOnly=yes"
```

Objetivo:

- Forzar que este repositorio use la clave SSH correcta al operar con `origin`.

Verificacion minima:

```powershell
git config --get core.sshCommand
```

Resultado esperado:

- Git devuelve `ssh -i C:/Users/Asus/.ssh/id_ed25519 -o IdentitiesOnly=yes`.

Comando:

```powershell
ssh -o BatchMode=yes -o StrictHostKeyChecking=accept-new -T git@github.com
```

Objetivo:

- Comprobar si la autenticacion SSH contra GitHub ya puede completarse sin interaccion.

Resultado observado:

- La conexion ya no falla por ACL de la clave, pero sigue devolviendo `Permission denied (publickey)` porque la clave requiere passphrase o todavia no esta habilitada para este acceso en GitHub.

Comando:

```powershell
git status --ignored --short
git ls-files
```

Objetivo:

- Verificar que solo queden ignorados los artefactos transitorios y que los datasets oficiales queden versionados.

Verificacion minima:

- `git status --ignored --short` mantiene ignorados `logs/`, `.venv/`, caches y `data/bronze/matchhistory/inbox`.
- `git ls-files` incluye `data/bronze/matchhistory/raw/*`, `data/bronze/matchhistory/manifests/*` y `data/silver/matches_silver.parquet`.

Comando:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Objetivo:

- Validar offline que el nuevo contrato de versionado no rompe tests ni contratos del proyecto.

Verificacion minima:

- La suite pasa sin depender de internet.

### 32. Optimizar el tiempo de los tests sin cambiar su cobertura funcional

Comandos:

```powershell
.\.venv\Scripts\python.exe -m pytest --durations=10 -q
.\.venv\Scripts\python.exe -m pytest
```

Objetivo:

- Medir los tests mas lentos y eliminar trabajo innecesario en las pruebas unitarias.
- Restringir el discovery de `pytest` a `tests/` para que no recorra el resto del repositorio.

Cambio aplicado:

- `pyproject.toml` ahora fija `testpaths = ["tests"]`.
- `tests\test_validate_rules.py` deja de escribir y leer un Parquet temporal en la prueba de rechazo de `silver` en raiz; esa prueba ahora usa un archivo placeholder y mockea `_read_dataset_frame`, porque el objetivo es validar la regla estructural y no el backend de I/O.

Verificacion minima:

```powershell
.\.venv\Scripts\python.exe -m pytest --durations=10 -q
```

Resultado esperado:

- La suite sigue pasando completa.
- El test `test_validate_managed_dataset_rejects_new_silver_stage_root_file` baja su costo al evitar I/O Parquet innecesario.
- `pytest` concentra el discovery en `tests/`.

### 33. Alinear los notebooks oficiales y eliminar checkpoints locales fuera del flujo

Comandos:

```powershell
Remove-Item -LiteralPath .\.ipynb_checkpoints -Recurse -Force
Remove-Item -LiteralPath .\notebooks\.ipynb_checkpoints -Recurse -Force
.\scripts\validate-project.ps1 -Scope project
```

Objetivo:

- Eliminar checkpoints locales de Jupyter que no son backups oficiales del proyecto.
- Dejar un unico criterio de respaldo para notebooks oficiales: `docs\notebooks\*_cells.md`.
- Hacer que la validacion estructural falle si reaparecen checkpoints locales fuera de `.venv`.

Verificacion minima:

- No existen `.ipynb_checkpoints` en la raiz del proyecto ni dentro de `notebooks`.
- `.\scripts\validate-project.ps1 -Scope project` pasa con el workspace limpio.

Resultado esperado:

- `01` y `02` quedan alineados bajo el mismo criterio de respaldo oficial.
- Los archivos `*-checkpoint.ipynb` dejan de considerarse parte aceptable del estado local del proyecto.
