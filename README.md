# parcial3-CPD-Proyecto

Sistema distribuido para preparar y analizar datos abiertos de accidentes de transito terrestre en zonas urbanas y suburbanas (ATUS) del INEGI. El proyecto sigue la arquitectura propuesta en el documento tecnico: Python, Pandas, Ray Core, Ray Data, Ray Cluster, Docker y Streamlit para la etapa de visualizacion.

Esta primera etapa cubre la recoleccion local de datos, limpieza, normalizacion, particionamiento distribuido y generacion de archivos listos para analisis estadistico y dashboard.

## Tecnologias

- Python 3.11 o 3.12
- Pandas
- Ray Core
- Ray Data
- PyArrow
- Docker
- Streamlit

Ray en Windows no cuenta con wheels para todas las versiones de Python. Para este proyecto se recomienda crear el entorno con Python 3.11 o 3.12. Python 3.14 no es compatible con la version de Ray definida en `requirements.txt`.

## Estructura del proyecto

```text
.
|-- conjunto_de_datos_atus_anual_csv/   # Datos ATUS descargados desde INEGI
|-- data/processed/                     # Salidas generadas por el pipeline
|-- docs/                               # Arquitectura y contrato de datos
|-- scripts/                            # Scripts auxiliares para Ray y ejecucion
|-- src/atus_pipeline/                  # Codigo fuente del pipeline
|-- Dockerfile
|-- docker-compose.ray.yml
|-- pyproject.toml
`-- requirements.txt
```

Las carpetas `conjunto_de_datos_atus_anual_csv/` y `data/` estan ignoradas por Git para evitar subir datos grandes o resultados generados.

## Datos de entrada

Antes de ejecutar el pipeline es necesario tener descargada la carpeta `conjunto_de_datos_atus_anual_csv/` en la raiz del proyecto. Esta carpeta contiene los CSV anuales de ATUS, catalogos, metadatos y diccionario de datos.

El pipeline espera la descarga anual de ATUS con esta estructura:

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

Cada archivo anual se procesa por bloques para evitar cargar todos los datos en memoria.

## Instalacion

Listar versiones disponibles de Python en Windows:

```powershell
py -0p
```

Crear y activar el entorno virtual con Python 3.11:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -e .
```

Para Python 3.12, usar:

```powershell
py -3.12 -m venv .venv
```

## Ejecucion rapida

Procesar una muestra pequena del año 2024:

```powershell
atus-pipeline --engine local --years 2024 --max-rows-per-file 10000
```

Este comando permite validar instalacion, lectura de datos, limpieza y generacion de salidas sin procesar todo el conjunto historico.

Por defecto, cada ejecucion regenera las carpetas `clean_csv/`, `clean_parquet/` y `summary/` dentro de `data/processed/`. Esto evita duplicados cuando se vuelve a correr el pipeline despues de una prueba o una ejecucion interrumpida. Para conservar salidas existentes y agregar nuevas particiones, usar `--append-output`.

## Ejecucion distribuida local con Ray

Procesar todos los años disponibles usando Ray:

```powershell
atus-pipeline --engine ray --years 1997-2024 --write-parquet
```

Tambien se puede ejecutar mediante el script auxiliar:

```powershell
.\scripts\run_pipeline.ps1 -Engine ray -Years "1997-2024" -WriteParquet
```

## Ray Cluster

Iniciar el head node:

```powershell
.\scripts\start_ray_head.ps1
```

Conectar cada worker node al head node:

```powershell
.\scripts\start_ray_worker.ps1 -HeadAddress "<ip-head>:6379"
```

Ejecutar el pipeline desde el head node:

```powershell
atus-pipeline --engine ray --ray-address auto --years 1997-2024 --write-parquet
```

## Docker

Construir la imagen:

```powershell
docker build -t atus-ray-pipeline .
```

Levantar Ray head, worker y ejecutar el pipeline:

```powershell
docker compose -f docker-compose.ray.yml up --build pipeline
```

## Arquitectura de procesamiento

El head node carga catalogos, descubre archivos anuales y divide el trabajo en tres nodos logicos siguiendo la arquitectura del proyecto:

- `worker_node_1_a_c`: estados A-C
- `worker_node_2_d_m`: estados D-M
- `worker_node_3_n_z`: estados N-Z

Cada worker lee los CSV por bloques, filtra las entidades asignadas, limpia los registros, agrega campos derivados y genera resultados parciales. El head node consolida los resumenes finales.

## Limpieza y normalizacion

El pipeline realiza las siguientes transformaciones:

- Estandarizacion de nombres de columnas.
- Limpieza de espacios, tabuladores y valores vacios.
- Conversion de codigos numericos y preservacion de claves con ceros a la izquierda.
- Normalizacion de fechas, horas y minutos.
- Enriquecimiento con catalogos de entidad y municipio.
- Calculo de victimas heridas, victimas fallecidas y total de victimas.
- Deteccion de accidentes con heridos, fallecidos, victimas y gravedad.
- Identificacion de registros `Certificado cero`.
- Generacion de trazabilidad por archivo fuente y worker node.

## Salidas

Las salidas se generan en `data/processed/`.

```text
data/processed/
|-- clean_csv/          # Particiones limpias en CSV
|-- clean_parquet/      # Particiones limpias en Parquet, si se usa --write-parquet
`-- summary/            # Agregados para analisis y dashboard
```

Resumenes disponibles:

- `accidents_by_state.csv`
- `accidents_by_municipality.csv`
- `accidents_by_hour.csv`
- `accidents_by_month.csv`
- `accidents_by_cause.csv`
- `accidents_by_type.csv`
- `accidents_by_classification.csv`
- `annual_trend.csv`
- `data_quality_report.csv`
- `run_metrics.csv`

## Uso con Ray Data

Las particiones limpias pueden cargarse como `ray.data.Dataset` para continuar con analisis distribuido o integracion con dashboard.

```python
from atus_pipeline.ray_dataset import load_clean_dataset

ds = load_clean_dataset("data/processed")
```

## Documentacion

- [Arquitectura](docs/arquitectura.md)
- [Contrato de datos limpios](docs/contrato_datos.md)

## Siguientes pasos

La siguiente etapa del proyecto puede continuar con:

1. Ejecutar el pipeline completo sobre 1997-2024 y validar `data_quality_report.csv`.
2. Revisar `run_metrics.csv` para comparar tiempo local contra Ray y calcular speedup.
3. Construir el analisis estadistico a partir de los resumenes en `data/processed/summary/`.
4. Crear el dashboard en Streamlit usando los agregados CSV y, si se requiere, `load_clean_dataset()`.
5. Agregar visualizaciones para rankings por entidad, municipio, hora, mes, causa, tipo de accidente y gravedad.
6. Documentar hallazgos principales y decisiones metodologicas en el reporte tecnico.
