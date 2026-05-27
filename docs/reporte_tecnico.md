# Reporte tecnico del proyecto ATUS con computo paralelo y distribuido

## 1. Resumen ejecutivo

Este proyecto implementa un sistema de procesamiento distribuido para preparar, limpiar, resumir y visualizar datos del conjunto ATUS del INEGI, correspondiente a Accidentes de Transito Terrestre en Zonas Urbanas y Suburbanas. La solucion se construyo en Python y utiliza Pandas para la transformacion de datos, Ray Core para distribuir el procesamiento entre nodos logicos, Ray Data como opcion de carga posterior de particiones limpias, y Streamlit con Plotly para el dashboard analitico.

El flujo general consiste en tomar los archivos CSV anuales descargados desde INEGI, leerlos por bloques, distribuir el trabajo por entidades federativas, normalizar la informacion, generar variables derivadas, producir archivos limpios en CSV y opcionalmente en Parquet, y crear resumenes estadisticos listos para el analisis y la visualizacion. El dashboard consume directamente los CSV agregados de `data/processed/summary/`, por lo que la etapa de procesamiento funciona como base de datos preparada para la etapa de analisis.

La arquitectura separa claramente las responsabilidades del proyecto: el pipeline distribuido se encarga de recoleccion local, limpieza, normalizacion, particionamiento, trazabilidad y agregacion; el dashboard se encarga de interpretar los resultados mediante indicadores, graficas, rankings, comparaciones temporales y mediciones de rendimiento.

## 2. Objetivo del proyecto

El objetivo principal es procesar un volumen grande de datos abiertos de accidentes viales de forma eficiente, reproducible y escalable. Para lograrlo, el proyecto aplica conceptos de computo paralelo y distribuido mediante Ray, dividiendo la carga entre tres nodos de trabajo. Cada nodo procesa una porcion de las entidades federativas, genera salidas parciales y entrega resultados al nodo principal, que consolida los resumenes finales.

Los objetivos especificos son:

- Recolectar y leer los archivos ATUS anuales desde una carpeta local descargada de INEGI.
- Limpiar y normalizar columnas, tipos de datos, fechas, horas, codigos geograficos y variables categoricas.
- Enriquecer los datos con catalogos oficiales de entidad y municipio.
- Calcular variables derivadas como total de vehiculos, victimas heridas, victimas fallecidas, accidentes con victimas e indice de gravedad.
- Distribuir el procesamiento usando Ray Core, simulando nodos de trabajo logicos.
- Generar archivos limpios y resumenes estadisticos para analisis posterior.
- Presentar los resultados en un dashboard interactivo con Streamlit y Plotly.

## 3. Datos utilizados

La fuente de datos es ATUS del INEGI. El proyecto espera que la carpeta `conjunto_de_datos_atus_anual_csv/` exista en la raiz del repositorio. Esta carpeta no se sube a GitHub porque contiene archivos grandes. Dentro de ella se espera una estructura similar a:

```text
conjunto_de_datos_atus_anual_csv/
|-- catalogos/
|-- conjunto_de_datos/
|   |-- atus_anual_1997.csv
|   |-- ...
|   `-- atus_anual_2024.csv
|-- diccionario_de_datos/
`-- metadatos/
```

Los archivos anuales se procesan desde `conjunto_de_datos/`, mientras que los catalogos se cargan desde `catalogos/`. Los catalogos permiten convertir codigos oficiales en nombres legibles, por ejemplo entidad federativa y municipio.

En la corrida disponible del proyecto se generaron 1,892,726 filas limpias. Los resumenes existentes incluyen los años 1999, 2010, 2022, 2023 y 2024. En esa ejecucion se leyeron 10,730,849 filas fuente y se procesaron con Ray en 143.07 segundos.

## 4. Tecnologias principales

El proyecto usa Python 3.11 o 3.12, debido a que Ray no cuenta con soporte para Python 3.14 en Windows. Las dependencias estan centralizadas en `requirements.txt` y en `pyproject.toml`.

Las tecnologias principales son:

- Python: lenguaje base del pipeline y del dashboard.
- Pandas: lectura por bloques, limpieza, transformaciones y agregaciones.
- NumPy: soporte numerico usado por el dashboard.
- Ray Core: ejecucion paralela de tareas remotas.
- Ray Data: carga opcional de particiones limpias como `ray.data.Dataset`.
- PyArrow: escritura de particiones Parquet cuando se usa `--write-parquet`.
- Streamlit: aplicacion web interactiva del dashboard.
- Plotly: graficas interactivas del dashboard.
- Docker y Docker Compose: ejecucion reproducible y opcion de cluster Ray en contenedores.

## 5. Arquitectura general

La arquitectura sigue un modelo head-worker. El nodo principal o head node coordina la ejecucion: carga los catalogos, descubre los archivos anuales, construye la asignacion de estados por nodo, lanza tareas paralelas y finalmente consolida los resultados. Los workers son tareas Ray que leen los CSV, filtran los registros de las entidades asignadas, limpian los datos y calculan resumenes parciales.

El flujo es:

1. Entrada local: archivos ATUS descargados desde INEGI.
2. Head node: inicializa la configuracion, carga catalogos y reparte el trabajo.
3. Workers Ray: procesan datos por bloques y por grupo de entidades.
4. Salidas limpias: particiones CSV y opcionalmente Parquet.
5. Resumenes estadisticos: CSV agregados para dashboard.
6. Dashboard Streamlit: visualizacion y analisis interactivo.

Esta arquitectura permite ejecutar el mismo proyecto de tres formas: modo local secuencial, modo Ray local en una sola computadora, o modo Ray Cluster con un head node y workers conectados.

## 6. Distribucion de procesos en Ray

La distribucion se define en `src/atus_pipeline/catalogs.py`, dentro de la funcion `build_state_node_shards`. El proyecto divide las entidades federativas en tres grupos segun la primera letra del nombre de la entidad:

- `worker_node_1_a_c`: estados cuyo nombre inicia de A a C.
- `worker_node_2_d_m`: estados cuyo nombre inicia de D a M.
- `worker_node_3_n_z`: estados cuyo nombre inicia de N a Z.

Esta division genera tres nodos logicos de procesamiento. En `src/atus_pipeline/pipeline.py`, la funcion `run_pipeline` convierte cada grupo en una tarea remota de Ray usando `ray.remote(_process_shard)`. Cada tarea recibe el listado completo de archivos anuales, la lista de entidades que le corresponde, los catalogos y las opciones de salida.

Cada worker ejecuta `_process_shard`, que realiza los siguientes pasos:

1. Lee cada archivo anual con `pd.read_csv` usando `chunksize`, para no cargar todo el archivo en memoria.
2. Estandariza los nombres de columnas originales.
3. Filtra las filas cuyo `ID_ENTIDAD` pertenece al grupo asignado.
4. Limpia el bloque filtrado con `clean_dataframe`.
5. Escribe particiones limpias en `data/processed/clean_csv/`.
6. Si se solicita, escribe tambien Parquet en `data/processed/clean_parquet/`.
7. Calcula resumenes parciales con `make_summaries`.
8. Registra metricas de calidad y rendimiento.

Al terminar, Ray devuelve al head node los resultados de cada worker. El head node ejecuta `_write_head_outputs`, combina los resumenes parciales y escribe los CSV finales en `data/processed/summary/`.

En modo `local`, los mismos tres shards se procesan de forma secuencial, lo que sirve como linea base. En modo `ray`, los shards se ejecutan en paralelo. En modo cluster se usa `--ray-address auto` para conectar el pipeline al head node de Ray.

## 7. Limpieza y normalizacion de datos

La limpieza principal esta en `src/atus_pipeline/cleaning.py`. La funcion central es `clean_dataframe`, que recibe un bloque Pandas ya filtrado por entidad y lo transforma en un esquema limpio.

Las reglas de limpieza incluyen:

- Estandarizacion de nombres de columnas a partir de los nombres originales de INEGI.
- Renombrado de columnas, por ejemplo `ANIO` se transforma en `año`.
- Limpieza de texto: elimina espacios extra, tabuladores, caracteres invisibles y valores vacios.
- Conversion segura de columnas numericas a enteros con valores nulos permitidos.
- Conservacion de claves geograficas con ceros a la izquierda, como `id_entidad` e `id_municipio`.
- Creacion de `cve_municipio` concatenando entidad y municipio.
- Validacion de hora, minuto, dia, mes y año.
- Generacion de `fecha` en formato `YYYY-MM-DD` cuando los componentes son validos.
- Generacion de `hora_minuto` cuando hora y minuto son validos.
- Calculo de `total_vehiculos`.
- Calculo de `victimas_muertas`, `victimas_heridas` y `total_victimas`.
- Identificacion de `es_certificado_cero`, que representa registros informativos sin accidente real.
- Clasificacion de zona como urbana, suburbana, certificado cero o no especificada.
- Creacion de banderas como `hay_muertos`, `hay_heridos`, `accidente_con_victimas` y `accidente_grave`.
- Enriquecimiento con catalogos de entidad y municipio.
- Agregado de trazabilidad con `fuente_archivo` y `worker_node`.

Esta etapa es importante porque convierte los datos originales, que vienen con codigos y valores especiales, en un conjunto consistente para analisis estadistico.

## 8. Salidas generadas

El pipeline genera todas las salidas dentro de `data/processed/`.

Las particiones limpias en CSV se escriben en:

```text
data/processed/clean_csv/<worker_node>/atus_clean_<año>_<worker_node>.csv
```

Si se usa `--write-parquet`, tambien se generan particiones en:

```text
data/processed/clean_parquet/<worker_node>/atus_clean_<año>_<worker_node>_part_<n>.parquet
```

Los resumenes estadisticos quedan en:

```text
data/processed/summary/
```

Los archivos de resumen son:

- `accidents_by_state.csv`: accidentes agregados por entidad federativa.
- `accidents_by_municipality.csv`: accidentes agregados por municipio.
- `accidents_by_hour.csv`: distribucion por hora.
- `accidents_by_weekday.csv`: distribucion por dia de la semana.
- `accidents_by_month.csv`: tendencia mensual por año.
- `accidents_by_zone.csv`: distribucion por zona urbana, suburbana o no especificada.
- `accidents_by_cause.csv`: ranking por causa.
- `accidents_by_type.csv`: ranking por tipo de accidente.
- `accidents_by_classification.csv`: fatal, no fatal y solo daños.
- `annual_trend.csv`: tendencia anual.
- `data_quality_report.csv`: filas leidas, seleccionadas, limpias y errores por archivo/nodo.
- `run_metrics.csv`: tiempo, motor y rendimiento por worker.

## 9. Metricas estadisticas calculadas

Los resumenes se calculan en `src/atus_pipeline/cleaning.py`, principalmente mediante `aggregate_dataframe` y `make_summaries`. Antes de agrupar, se excluyen los registros `Certificado cero`, ya que no representan accidentes reales.

Las metricas principales son:

- `accidentes`: numero de registros ATUS validos para analisis.
- `accidentes_con_heridos`: accidentes con una o mas victimas heridas.
- `accidentes_con_muertos`: accidentes con una o mas victimas fallecidas.
- `victimas_heridas`: suma total de heridos.
- `victimas_muertas`: suma total de fallecidos.
- `total_victimas`: heridos mas fallecidos.
- `indice_gravedad`: indicador ponderado de severidad.

El indice de gravedad se define como:

```text
indice_gravedad = (victimas_heridas + victimas_muertas * 5) / accidentes
```

La formula asigna mayor peso a los fallecimientos que a los heridos. Esto permite comparar territorios o tipos de accidente no solo por volumen, sino por severidad relativa. Un estado con pocos accidentes puede ser mas critico si su indice de gravedad es alto.

## 10. Analisis estadistico aplicado

El analisis estadistico se realiza en dos niveles. Primero, el pipeline genera agregaciones limpias y reproducibles. Segundo, el dashboard interpreta esas agregaciones con visualizaciones, comparaciones y rankings.

Los analisis principales son:

### 10.1 Tendencia anual

Se usa `annual_trend.csv` para observar la evolucion de accidentes, heridos, fallecidos e indice de gravedad por año. En la corrida disponible, los accidentes aumentaron de 285,494 en 1999 a 427,267 en 2010, y despues se observa un descenso en 2022-2024. El indice de gravedad bajo de 0.460286 en 1999 a 0.291400 en 2024, lo cual indica una mejora relativa en severidad.

### 10.2 Analisis por estado

Se usa `accidents_by_state.csv` para ordenar entidades por volumen, victimas e indice de gravedad. En los resultados actuales, Nuevo Leon concentra 354,631 accidentes, seguido por Chihuahua con 151,300 y Jalisco con 132,350. Sin embargo, el dashboard tambien compara gravedad, porque el estado con mas accidentes no necesariamente es el mas severo.

### 10.3 Analisis por municipio

Se usa `accidents_by_municipality.csv` para identificar municipios con alta siniestralidad y municipios con alto indice de gravedad. El dashboard permite filtrar por numero minimo de accidentes para evitar interpretar municipios con muy pocos registros como casos extremos sin suficiente base estadistica.

### 10.4 Distribucion horaria

Se usa `accidents_by_hour.csv` para detectar horas de mayor concentracion de accidentes. En la corrida disponible, las horas con mas accidentes incluyen 14:00, 15:00, 18:00, 16:00 y 19:00. El dashboard tambien analiza turnos del dia y severidad por hora, permitiendo observar diferencias entre volumen y gravedad.

### 10.5 Distribucion por dia de la semana

Se usa `accidents_by_weekday.csv` para cubrir el analisis de dias con mayor riesgo, mencionado en el PDF. Este resumen permite comparar volumen de accidentes e indice de gravedad por lunes, martes, miercoles, jueves, viernes, sabado y domingo. En el dashboard aparece dentro de la seccion de distribucion horaria, porque ambos analisis describen patrones temporales.

### 10.6 Tendencia mensual

Se usa `accidents_by_month.csv` para comparar accidentes, heridos, fallecidos e indice de gravedad por mes y por año. El dashboard permite revisar valores por año, promedios mensuales y mapas de calor.

### 10.7 Analisis por zona

Se usa `accidents_by_zone.csv` para responder la pregunta del PDF sobre donde hay mas victimas heridas o fallecidas por zona y gravedad. El dashboard compara accidentes, heridos, fallecidos, total de victimas e indice de gravedad para zonas urbanas, suburbanas, no especificadas o registros clasificados como certificado cero cuando aplique.

### 10.8 Causas de accidente

Se usa `accidents_by_cause.csv`. En la corrida disponible, la causa principal es `Conductor`, con 1,694,236 accidentes. Le siguen `Otra`, `Mala condicion del camino`, `Falla del vehiculo` y `Peaton o pasajero`. Este analisis permite distinguir entre factores humanos, infraestructura, vehiculo y otros factores.

### 10.9 Tipo de accidente

Se usa `accidents_by_type.csv`. El tipo con mayor volumen es `Colision con vehiculo automotor`, con 1,181,282 accidentes. Tambien aparecen tipos relevantes como colision con motocicleta, colision con objeto fijo, atropellamiento, salida del camino y volcadura. El dashboard cruza volumen con gravedad para identificar eventos de mayor riesgo relativo.

### 10.10 Clasificacion del accidente

Se usa `accidents_by_classification.csv` para comparar accidentes fatales, no fatales y de solo daños. En la corrida actual hay 23,378 accidentes fatales, 361,322 no fatales y 1,461,289 de solo daños. Este analisis ayuda a separar cantidad de accidentes de severidad real.

### 10.11 Rendimiento Ray vs Pandas

Se usa `run_metrics.csv` y `data_quality_report.csv`. El dashboard compara el tiempo total de Ray contra un estimado secuencial basado en la suma de tiempos de los workers. En la corrida disponible, Ray proceso la carga en 143.07 segundos. Los tres workers limpiaron:

- `worker_node_1_a_c`: 452,325 filas en 114.14 segundos.
- `worker_node_2_d_m`: 520,463 filas en 119.64 segundos.
- `worker_node_3_n_z`: 919,938 filas en 135.97 segundos.

Esto muestra un desbalance de carga: el nodo N-Z procesa mas filas que los otros. Aun asi, Ray reduce el tiempo total porque los tres trabajos se ejecutan en paralelo. La comparacion es util para demostrar el beneficio de la paralelizacion y tambien para discutir oportunidades de mejora en el particionamiento.

## 11. Dashboard

El dashboard esta implementado en `dashboard.py`. Usa Streamlit como interfaz y Plotly para graficas interactivas. Carga los datos desde `data/processed/summary/` mediante `pd.read_csv`.

Las secciones del dashboard son:

- Resumen General: KPIs globales, evolucion anual y clasificacion de accidentes.
- Analisis por Estado: ranking por volumen, ranking por gravedad y tabla comparativa.
- Analisis por Municipio: top por volumen, top por gravedad y busqueda en tabla.
- Distribucion Horaria: accidentes por hora, analisis por turno y mapas de calor.
- Distribucion por Dia de Semana: comparacion temporal por dia e indice de gravedad.
- Tendencia Mensual: comparacion mensual por año, promedio mensual y mapa de calor.
- Causas y Tipos: ranking por causa, treemap por tipo y relacion volumen-gravedad.
- Victimas y Gravedad: comparacion de heridos, fallecidos, zona e indice de gravedad.
- Ray vs Pandas: metricas de rendimiento, speedup, throughput y carga por worker.

El dashboard no vuelve a limpiar los datos. Su funcion es leer los resumenes ya preparados por el pipeline. Por eso es necesario ejecutar primero el pipeline y generar `data/processed/summary/`.

## 12. Archivos importantes del proyecto

Los archivos principales son:

- `README.md`: instrucciones generales de instalacion, ejecucion del pipeline, Ray Cluster, Docker y dashboard.
- `requirements.txt`: dependencias necesarias para pipeline y dashboard.
- `pyproject.toml`: metadatos del paquete, version de Python soportada, dependencias y comando `atus-pipeline`.
- `dashboard.py`: dashboard interactivo con Streamlit y Plotly.
- `src/atus_pipeline/config.py`: columnas originales, renombrado de columnas, columnas de salida, metricas y opciones del pipeline.
- `src/atus_pipeline/catalogs.py`: carga de catalogos de INEGI y construccion de shards por nodos Ray.
- `src/atus_pipeline/cleaning.py`: reglas de limpieza, variables derivadas y agregaciones estadisticas.
- `src/atus_pipeline/pipeline.py`: orquestacion principal, procesamiento local o Ray, escritura de salidas y consolidacion.
- `src/atus_pipeline/cli.py`: interfaz de linea de comandos para ejecutar el pipeline.
- `src/atus_pipeline/ray_dataset.py`: helper para cargar particiones limpias como Ray Data.
- `scripts/run_pipeline.ps1`: script auxiliar para ejecutar el pipeline en PowerShell.
- `scripts/start_ray_head.ps1`: inicia el head node de Ray.
- `scripts/start_ray_worker.ps1`: conecta un worker node al head node.
- `Dockerfile`: imagen del proyecto.
- `docker-compose.ray.yml`: ejecucion con Ray head, worker y pipeline en contenedores.
- `docs/arquitectura.md`: descripcion de arquitectura y diagrama extraido del PDF.
- `docs/contrato_datos.md`: contrato de datos limpios, columnas y resumenes generados.
- `.gitignore`: evita subir datos grandes, entornos virtuales y salidas generadas.

## 13. Ejecucion del proyecto

Para instalar el proyecto se recomienda Python 3.11 o 3.12:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip install -e .
```

Para una prueba rapida:

```powershell
atus-pipeline --engine local --years 2024 --max-rows-per-file 10000
```

Para ejecutar con Ray local:

```powershell
atus-pipeline --engine ray --years 1997-2024 --write-parquet
```

Para ejecutar contra un Ray Cluster:

```powershell
.\scripts\start_ray_head.ps1
.\scripts\start_ray_worker.ps1 -HeadAddress "<ip-head>:6379"
atus-pipeline --engine ray --ray-address auto --years 1997-2024 --write-parquet
```

Para abrir el dashboard:

```powershell
.\.venv\Scripts\python.exe -m streamlit run dashboard.py
```

## 14. Calidad, trazabilidad y reproducibilidad

El proyecto registra trazabilidad en cada fila limpia mediante `fuente_archivo` y `worker_node`. Esto permite saber de que archivo anual provino un registro y que nodo lo proceso. Ademas, `data_quality_report.csv` resume por archivo y worker la cantidad de filas leidas, seleccionadas, limpiadas, certificados cero, fechas invalidas, horas invalidas y tiempo de procesamiento.

La reproducibilidad se logra con:

- Dependencias centralizadas en `requirements.txt`.
- Instalacion editable mediante `pyproject.toml`.
- CLI estable con `atus-pipeline`.
- Separacion clara entre datos crudos, salidas limpias y resumenes.
- Documentacion en `README.md`, `docs/arquitectura.md` y `docs/contrato_datos.md`.
- Opciones de ejecucion local, Ray local, Ray Cluster y Docker.

## 15. Observaciones tecnicas

Una observacion importante es que cada worker lee los archivos anuales y despues filtra las entidades asignadas. Esto simplifica la arquitectura y evita conflictos entre workers, pero implica que existe lectura repetida de los archivos fuente. Aun asi, al ejecutar las transformaciones en paralelo, el tiempo total disminuye respecto a una ejecucion secuencial.

Tambien se observa desbalance de carga entre nodos, porque la division alfabetica de estados no garantiza la misma cantidad de registros por grupo. El worker N-Z procesa mas filas que los demas. Una mejora futura podria repartir por volumen historico de registros o por particiones mas pequenas para equilibrar mejor el trabajo.

Otra decision relevante es conservar los registros de `Certificado cero` en los datos limpios, pero excluirlos de los resumenes estadisticos. Esto mantiene trazabilidad completa sin contaminar los indicadores de accidentes reales.

## 16. Cumplimiento contra el PDF del proyecto

El proyecto satisface los elementos principales solicitados en el PDF:

- Plataforma distribuida en Python con Ray y Ray Cluster: implementada mediante `src/atus_pipeline/pipeline.py`, scripts de Ray y `docker-compose.ray.yml`.
- Uso de datos abiertos ATUS de INEGI: se trabaja con la carpeta `conjunto_de_datos_atus_anual_csv/`.
- Preparacion de datos historicos: el pipeline descubre archivos `atus_anual_*.csv` y permite seleccionar años o rangos.
- Limpieza y normalizacion: implementada en `src/atus_pipeline/cleaning.py`.
- Distribucion por entidad, bloques y workers: implementada con tres shards logicos A-C, D-M y N-Z.
- Calculo de estadisticas agregadas: implementado con resumenes por estado, municipio, hora, dia de semana, mes, zona, causa, tipo, clasificacion y tendencia anual.
- Deteccion de patrones de riesgo: cubierta en el dashboard por ubicacion, temporalidad, causa, tipo, victimas y gravedad.
- Comparacion Ray vs Pandas secuencial: cubierta en la seccion `Ray vs Pandas` del dashboard con tiempos, throughput y speedup.
- Productos finales: dataset preparado en CSV/Parquet, script con Ray, dashboard interactivo y reporte tecnico.

La revision contra el PDF mostro dos oportunidades de mejora: agregar resumen por dia de semana y resumen por zona. Ambos fueron incorporados al pipeline y al dashboard para cubrir mejor las preguntas de analisis sobre dias de mayor riesgo y victimas por zona/gravedad.

## 17. Conclusiones

El proyecto cumple con una arquitectura de computo paralelo y distribuido aplicada a datos reales de INEGI. La solucion no solo procesa los CSV de ATUS, sino que los convierte en un conjunto limpio, enriquecido y analiticamente util. Ray permite dividir el trabajo en nodos logicos y ejecutar tareas en paralelo, mientras que Pandas aporta flexibilidad para limpiar y agregar datos por bloques.

La etapa estadistica transforma los registros individuales en indicadores comprensibles: accidentes, heridos, fallecidos, total de victimas e indice de gravedad. Estos indicadores permiten comparar años, estados, municipios, horas, causas, tipos de accidente y clasificaciones. El dashboard completa el proyecto al convertir los resultados en una herramienta visual para explorar patrones de siniestralidad vial y rendimiento del procesamiento distribuido.

En conjunto, el proyecto demuestra un flujo completo de ingenieria de datos: entrada cruda, procesamiento distribuido, limpieza, enriquecimiento, agregacion, medicion de calidad, analisis estadistico y visualizacion final.
