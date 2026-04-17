# Como continuar el ETL de MatchHistory

## Objetivo

Esta guia define el criterio durable para seguir el trabajo de ETL sin mezclar exploracion, automatizacion y documentacion viva.

El estado operativo actual del proyecto no se documenta aca. Para eso usar:

- `docs/generated/project-status.md` para estado local derivado
- `docs/generated/official-commands.md` para comandos oficiales
- `BITACORA_ENTORNO.md` para la receta operativa generada

## Postura de trabajo recomendada

- Mantener la ingesta en scripts y modulos de `bronze`.
- Usar notebooks oficiales solo para exploracion local y transformacion exploratoria.
- Consolidar en codigo versionado toda transformacion que gane un segundo consumidor, automatizacion o reutilizacion fuera del notebook.
- Mantener separadas las capas `bronze`, `silver` y `gold` por ownership y por contrato.

## Orden recomendado

### 1. Cerrar Bronze primero

- Confirmar que la ingesta oficial deja CSV canonicos y manifests consistentes.
- Explorar Bronze desde el notebook oficial, no desde llamadas online.
- Tratar los archivos de `inbox` como staging transitorio, no como dataset canonico.

### 2. Usar Silver como laboratorio controlado

- Empezar con una tabla limpia minima y entendible.
- Evitar renombrados masivos o features complejas mientras todavia se esta entendiendo el dataset.
- Mantener la logica en notebook solo mientras siga siendo exploratoria y con un unico consumidor.

### 3. Promover a codigo cuando el criterio ya sea estable

- Si la transformacion deja de ser exploratoria, moverla a `src/football_ml/` + `scripts/*`.
- Si aparece un segundo dataset `silver` oficial, dejar de escribirlo en la raiz del stage.
- No iniciar `gold` desde notebook.

## Reglas practicas para seguir

- Trabajar primero con temporadas cerradas antes de sumar temporadas en curso.
- Tratar odds y otras fuentes auxiliares como extensiones posteriores, no como punto de partida.
- Evitar leakage: resultados finales y variables post-partido no deben usarse como features pre-partido.
- Antes de promover una transformacion, verificar unicidad logica, consistencia temporal y tipos correctos.

## Salida del notebook hacia codigo

Mover una transformacion a codigo cuando se cumpla esto:

- las columnas finales ya estan decididas
- la clave logica del dataset es estable
- la transformacion puede rerunearse sobre nuevas temporadas sin cambios manuales
- ya existe necesidad de reutilizacion fuera del notebook

## Referencias

- Reglas de escalado: [reglas-escalado-seguro.md](./reglas-escalado-seguro.md)
- Estado operativo derivado: [../generated/project-status.md](../generated/project-status.md)
- Comandos oficiales: [../generated/official-commands.md](../generated/official-commands.md)
- Research primaria de `soccerdata`: [../research/soccer-deep-research-report.md](../research/soccer-deep-research-report.md)
