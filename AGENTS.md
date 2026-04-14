# Reglas operativas para agentes

## Documentacion de comandos

- Documentar siempre los comandos correctos que efectivamente funcionaron en este proyecto.
- Registrar los comandos en orden cronologico y metodologico.
- Usar una bitacora Markdown en la raiz del proyecto para dejar la receta reproducible del entorno y sus cambios operativos.
- Si un comando falla y luego se corrige, registrar solo la version correcta como receta final y dejar la fallida unicamente como nota de correccion o advertencia.

## Reglas para Python en Windows

- Usar siempre el interprete del entorno virtual de forma explicita: `.\.venv\Scripts\python.exe`.
- Instalar paquetes con `.\.venv\Scripts\python.exe -m pip ...`.
- No usar `pip` global ni asumir que el entorno esta activado.
- Cuando se actualicen dependencias directas del proyecto, tratarlas primero en `pyproject.toml` y luego resincronizar `requirements.txt`.
- Para notebooks de este proyecto, usar el kernel dedicado `football-ml (.venv)` en lugar del kernel generico `python3`.
- Usar `.\scripts\bootstrap.ps1`, `.\scripts\validate-project.ps1`, `.\scripts\sync-project.ps1`, `.\scripts\scaffold-notebook.ps1`, `.\scripts\ingest-matchhistory.ps1`, `.\scripts\refresh-matchhistory.ps1` y `.\scripts\export-notebook-cells.ps1` como interfaces oficiales del proyecto en Windows.
- Ejecutar los tests del proyecto con `.\.venv\Scripts\python.exe -m pytest`.

## Regla de mantenimiento de la bitacora

- Cada intervencion que cambie el entorno, las dependencias o la forma correcta de ejecutar el proyecto debe actualizar la bitacora Markdown existente.
- Cada cambio del proyecto debe revisar y actualizar tambien las secciones impactadas para que codigo, notebooks, exports, guias, reglas y bitacora reflejen el estado real vigente.
- No se debe cerrar un cambio si alguna seccion afectada queda desalineada respecto del estado actual del proyecto.
- La bitacora debe incluir:
  - comando ejecutado
  - objetivo del comando
  - resultado esperado o verificacion minima
  - correcciones relevantes si hubo un comando invalido previo
- Antes de cerrar cualquier cambio documental o de notebook, hacer una revision final de mojibakes en los archivos modificados.
- En esa revision, buscar secuencias visibles tipicas de texto mal decodificado y otros signos de mojibake en los archivos modificados.
- No dar por finalizada una tarea documental si queda texto visible con mojibake.
- La revision de mojibakes debe hacerse solo sobre archivos fuente del proyecto, excluyendo `.venv`, binarios, `__pycache__`, checkpoints y otros artefactos no fuente.

## Regla obligatoria anti-mojibake

- Con cada cambio realizado, verificar siempre antes de cerrar la tarea que no queden mojibakes visibles en los archivos fuente modificados.
- Esta verificacion final aplica aunque el cambio no sea documental y aunque no involucre notebooks.
- Si aparece texto mal decodificado, la tarea no se considera terminada hasta corregirlo y volver a verificar.
- La verificacion anti-mojibake forma parte del cierre obligatorio de cada cambio del proyecto, junto con la revision de alineacion de las secciones impactadas.

## Ubicacion de documentacion tecnica

- Los reportes de investigacion, analisis profundos de librerias, comparativas y documentos tecnicos de referencia deben guardarse en `docs/research`.
- Los notebooks exploratorios van en `notebooks`; la documentacion tecnica no debe mezclarse con notebooks ni con datos.
- La documentacion generada que replica o exporta codigo de notebooks debe guardarse en `docs/notebooks`.
- Las guias operativas, roadmaps de continuacion y documentos manuales de "que hacer despues" deben guardarse en `docs/guides`.
- Esa documentacion generada debe incluir el codigo de las celdas y los outputs textuales guardados del notebook, sin depender de HTML crudo.
- `docs/guides/reglas-escalado-seguro.md` es la referencia operativa para reglas de escalado del proyecto.

## Regla de fuente oficial por tipo de activo

- `AGENTS.md` define reglas operativas obligatorias.
- `BITACORA_ENTORNO.md` registra comandos y cambios operativos reproducibles.
- `config/project_governance.toml` define el entorno gobernado y el registro oficial de notebooks.
- `docs/guides/*` explica como operar o continuar.
- `docs/notebooks/*` solo replica notebooks oficiales y `docs/notebooks/README.md` inventaria los registrados.
- `src/football_ml/*` y `scripts/*` son la implementacion oficial.
- `pyproject.toml` es la fuente primaria de dependencias directas y `requirements.txt` es su artefacto sincronizado.
- Si una regla o flujo aparece en dos lugares, uno debe tratarse como fuente primaria y el otro debe referenciarlo, no redefinirlo con variaciones.

## Regla de ownership por capa

- `bronze` pertenece a scripts y modulos de ingesta, no a notebooks.
- `silver` puede seguir owned por notebook solo mientras sea exploratoria y tenga un solo consumidor.
- En cuanto una transformacion tenga segundo consumidor, automatizacion o reutilizacion fuera del notebook, su ownership migra a `src/football_ml/` + `scripts/*`.
- `gold` no debe nacer como ownership de notebook.

## Regla de contratos minimos de dataset

- Todo dataset oficial debe registrarse en codigo con nombre canonico, stage, path oficial, columnas minimas requeridas, clave logica o criterio de unicidad y politica de actualizacion.
- La validacion del proyecto debe revisar esos contratos contra el archivo oficial cuando el dataset exista localmente.
- Las excepciones transitorias de estructura, como un dataset `silver` en la raiz del stage, deben quedar documentadas en codigo y en guias.

## Regla de estructura escalable de datos

- Los datasets nuevos en `data/silver` y `data/gold` no deben crearse como archivos sueltos en la raiz del stage.
- Los nuevos datasets oficiales deben ir namespaced por dominio, por ejemplo `data/silver/matchhistory/...`.
- `data/silver/matches_silver.parquet` queda como excepcion transitoria documentada hasta que exista un segundo dataset `silver` oficial.

## Regla de alineacion para notebooks oficiales

- `notebooks/01_explorer_matchhistory.ipynb` es la referencia oficial de estilo y estructura para los notebooks futuros.
- Todo notebook oficial nuevo debe seguir el patron de nombre `NN_<etapa>_<tema>.ipynb`.
- Todo notebook oficial nuevo debe darse de alta desde `config/project_governance.toml`, preferentemente usando `.\scripts\scaffold-notebook.ps1`.
- Todo notebook oficial debe usar el kernel `football-ml (.venv)` y validar explicitamente `PROJECT_ROOT`, `EXPECTED_PYTHON` y `sys.executable` en la primera celda.
- Toda celda de codigo debe empezar con encabezados numerados estilo `01`: separador, titulo en espanol y comentario corto que explique el objetivo de la celda.
- Los IDs de celdas de notebooks oficiales deben ser slugs descriptivos, estables y sin valores aleatorios.
- Los notebooks oficiales solo pueden leer datos locales del proyecto; la ingesta online y las descargas quedan fuera del notebook y se ejecutan desde los scripts oficiales.
- Los notebooks oficiales conservan los outputs guardados que documentan el estado validado de cada etapa; si cambia codigo u output, hay que resincronizar sus artefactos generados.
- Si cambia cualquier notebook oficial gestionado por el proyecto, ejecutar `.\scripts\sync-project.ps1` antes de cerrar la tarea para regenerar `docs/notebooks/*_cells.md`, `docs/notebooks/README.md` y revisar la sincronizacion de dependencias.
- Antes de cerrar cambios en notebooks oficiales, ejecutar `.\scripts\validate-project.ps1 -Scope project` para validar kernel, bootstrap, manifiesto, inventario, Markdown generado y revision anti-mojibake.

## Regla para artefactos generados

- Los artefactos generados locales no deben mantenerse manualmente como fuente versionada del proyecto.
- `*.egg-info/` debe tratarse como salida local de instalacion editable y quedar fuera del versionado del repositorio.
- Los `.ipynb_checkpoints`, `.pytest_cache` y otros artefactos generados del flujo local tampoco deben quedar versionados.

## Regla de testing y cierre de cambio

- Cada cambio debe revisar su impacto en codigo, config, notebook oficial, export Markdown, guia operativa, bitacora, validacion y tests.
- Si una de esas secciones fue impactada y no se actualiza, el cambio queda incompleto.
- `validate-project.ps1` sigue siendo el gate estructural del proyecto.
- `sync-project.ps1` es el gate de sincronizacion de artefactos generados del proyecto.
- `.\.venv\Scripts\python.exe -m pytest` pasa a ser el gate funcional offline y ligero para contratos y smoke tests.
- No agregar tests que requieran internet para el camino normal del proyecto.

## Regla de automatizacion y observabilidad

- Toda automatizacion oficial debe ejecutar scripts, no notebooks.
- Toda automatizacion debe leer config oficial, escribir log local y dejar evidencia minima de estado o manifest.
- Debe existir una sola tarea programada oficial por workflow activo.

## Regla de consulta para soccerdata

- Cuando se necesite profundizar sobre la libreria `soccerdata`, su API, fuentes soportadas, metodos, limitaciones o riesgos operativos, consultar primero `docs/research/soccer-deep-research-report.md`.
- Ese documento debe tratarse como referencia interna primaria del proyecto para decisiones y respuestas relacionadas con `soccerdata`.
- Si el documento no alcanza para resolver una duda concreta, complementar despues con la documentacion oficial o con validaciones adicionales, pero no omitir la consulta inicial del reporte interno.
- En notebooks o scripts de scraping con `soccerdata`, configurar `data_dir` dentro de `data/bronze/...` para que el cache y los datos raw queden dentro de la estructura del proyecto.
- Si `MatchHistory` devuelve `HTTP 503` o `ConnectionError` al leer `football-data.co.uk`, tratarlo primero como una indisponibilidad temporal del proveedor externo, no como una falla local de dependencias o de sintaxis.
- La ingesta oficial no debe quedar implementada en notebooks. Los notebooks leen y exploran datos persistidos en `data/bronze/...`; la descarga y validacion se ejecutan desde los scripts oficiales.
- Cuando falle la descarga automatica de `MatchHistory`, el fallback manual debe usar `data/bronze/matchhistory/inbox` y nombres exactos `E0_<temporada>.csv`.
- El refresh diario debe mantener un unico CSV canonico por temporada en `data/bronze/matchhistory/raw` y reemplazarlo solo si cambia el checksum.

