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
- Cuando se actualicen dependencias directas del proyecto, reflejarlas en `requirements.txt`.
- Para notebooks de este proyecto, usar el kernel dedicado `football-ml (.venv)` en lugar del kernel generico `python3`.
- Usar `.\scripts\bootstrap.ps1`, `.\scripts\validate-project.ps1` y `.\scripts\ingest-matchhistory.ps1` como interfaces oficiales del proyecto en Windows.

## Regla de mantenimiento de la bitacora

- Cada intervencion que cambie el entorno, las dependencias o la forma correcta de ejecutar el proyecto debe actualizar la bitacora Markdown existente.
- La bitacora debe incluir:
  - comando ejecutado
  - objetivo del comando
  - resultado esperado o verificacion minima
  - correcciones relevantes si hubo un comando invalido previo
- Antes de cerrar cualquier cambio documental o de notebook, hacer una revision final de mojibakes en los archivos modificados.
- En esa revision, buscar secuencias visibles tipicas de texto mal decodificado y otros signos de mojibake en los archivos modificados.
- No dar por finalizada una tarea documental si queda texto visible con mojibake.
- La revision de mojibakes debe hacerse solo sobre archivos fuente del proyecto, excluyendo `.venv`, binarios, `__pycache__`, checkpoints y otros artefactos no fuente.

## Ubicacion de documentacion tecnica

- Los reportes de investigacion, analisis profundos de librerias, comparativas y documentos tecnicos de referencia deben guardarse en `docs/research`.
- Los notebooks exploratorios van en `notebooks`; la documentacion tecnica no debe mezclarse con notebooks ni con datos.

## Regla de consulta para soccerdata

- Cuando se necesite profundizar sobre la libreria `soccerdata`, su API, fuentes soportadas, metodos, limitaciones o riesgos operativos, consultar primero `docs/research/soccer-deep-research-report.md`.
- Ese documento debe tratarse como referencia interna primaria del proyecto para decisiones y respuestas relacionadas con `soccerdata`.
- Si el documento no alcanza para resolver una duda concreta, complementar despues con la documentacion oficial o con validaciones adicionales, pero no omitir la consulta inicial del reporte interno.
- En notebooks o scripts de scraping con `soccerdata`, configurar `data_dir` dentro de `data/bronze/...` para que el cache y los datos raw queden dentro de la estructura del proyecto.
- Si `MatchHistory` devuelve `HTTP 503` o `ConnectionError` al leer `football-data.co.uk`, tratarlo primero como una indisponibilidad temporal del proveedor externo, no como una falla local de dependencias o de sintaxis.
- La ingesta oficial no debe quedar implementada en notebooks. Los notebooks leen y exploran datos persistidos en `data/bronze/...`; la descarga y validacion se ejecutan desde los scripts oficiales.
- Cuando falle la descarga automatica de `MatchHistory`, el fallback manual debe usar `data/bronze/matchhistory/inbox` y nombres canonicos `eng_premier_league_<temporada>.csv`.

