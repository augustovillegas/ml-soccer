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
Get-ChildItem AGENTS.md, BITACORA_ENTORNO.md, .\docs\research\README.md, .\docs\research\soccer-deep-research-report.md, .\notebooks\01_explorer_matchhistory.ipynb | Select-String -Pattern 'fÃ|librerÃ|cachÃ|versiÃ|estÃ|mÃ|Ã¡|Ã©|Ã­|Ã³|Ãº|Ã±'
```

Resultado esperado:

- Sin coincidencias en los archivos fuente revisados
