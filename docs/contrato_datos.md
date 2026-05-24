# Contrato de datos limpios

Los archivos limpios se escriben en:

`data/processed/clean_csv/<worker_node>/atus_clean_<anio>_<worker_node>.csv`

Si se activa Parquet:

`data/processed/clean_parquet/<worker_node>/atus_clean_<anio>_<worker_node>_part_<n>.parquet`

## Columnas principales

- `anio`, `mes`, `dia`, `fecha`: fecha normalizada del accidente. Si INEGI marca dia no especificado, `fecha` queda vacia.
- `hora`, `minuto`, `hora_minuto`: hora normalizada. Si INEGI usa 99 como no especificado, queda vacia.
- `id_entidad`, `entidad`, `id_municipio`, `municipio`, `cve_municipio`: ubicacion enriquecida con catalogos.
- `zona`: `Urbana`, `Suburbana`, `Certificado cero` o `No especificada`.
- `tipo_accidente`, `causa_accidente`, `clasificacion_accidente`: categorias principales para ranking.
- `edad_codigo`, `edad_conductor`: `edad_codigo` conserva el codigo original; `edad_conductor` solo conserva edades validas 12-98.
- columnas de vehiculos: `automovil`, `motocicleta`, `bicicleta`, etc.
- columnas de victimas: muertos y heridos por conductor, pasajero, peaton, ciclista, otros y no especificados.
- `victimas_muertas`, `victimas_heridas`, `total_victimas`: totales derivados.
- `hay_muertos`, `hay_heridos`, `accidente_con_victimas`, `accidente_grave`: banderas para filtros del dashboard.
- `es_certificado_cero`: registros informativos sin accidente; se conservan en limpio, pero no cuentan en resumenes.
- `fuente_archivo`, `worker_node`: trazabilidad de procesamiento.

## Resumenes disponibles

Todos quedan en `data/processed/summary/`.

- `accidents_by_state.csv`: ranking por entidad federativa.
- `accidents_by_municipality.csv`: ranking municipal.
- `accidents_by_hour.csv`: distribucion por hora.
- `accidents_by_month.csv`: tendencia mensual por anio.
- `accidents_by_cause.csv`: ranking de causas.
- `accidents_by_type.csv`: ranking por tipo de accidente.
- `accidents_by_classification.csv`: fatal, no fatal, solo danos, etc.
- `annual_trend.csv`: tendencia anual.
- `data_quality_report.csv`: filas leidas, seleccionadas, limpias e incidencias de calidad por archivo/nodo.
- `run_metrics.csv`: tiempos y throughput por worker.

## Metricas de resumen

- `accidentes`: registros ATUS, excluyendo certificados cero.
- `accidentes_con_heridos`: accidentes con una o mas victimas heridas.
- `accidentes_con_muertos`: accidentes con una o mas victimas mortales.
- `victimas_heridas`: suma de personas heridas.
- `victimas_muertas`: suma de personas fallecidas.
- `total_victimas`: heridos + muertos.
- `indice_gravedad`: `(victimas_heridas + victimas_muertas * 5) / accidentes`.

