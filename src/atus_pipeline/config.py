"""Shared configuration for the ATUS cleaning pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


RAW_DATA_SUBDIR = Path("conjunto_de_datos")
CATALOG_SUBDIR = Path("catalogos")

RAW_COLUMNS = [
    "COBERTURA",
    "ID_ENTIDAD",
    "ID_MUNICIPIO",
    "ANIO",
    "MES",
    "ID_HORA",
    "ID_MINUTO",
    "ID_DIA",
    "DIASEMANA",
    "URBANA",
    "SUBURBANA",
    "TIPACCID",
    "AUTOMOVIL",
    "CAMPASAJ",
    "MICROBUS",
    "PASCAMION",
    "OMNIBUS",
    "TRANVIA",
    "CAMIONETA",
    "CAMION",
    "TRACTOR",
    "FERROCARRI",
    "MOTOCICLET",
    "BICICLETA",
    "OTROVEHIC",
    "CAUSAACCI",
    "CAPAROD",
    "SEXO",
    "ALIENTO",
    "CINTURON",
    "ID_EDAD",
    "CONDMUERTO",
    "CONDHERIDO",
    "PASAMUERTO",
    "PASAHERIDO",
    "PEATMUERTO",
    "PEATHERIDO",
    "CICLMUERTO",
    "CICLHERIDO",
    "OTROMUERTO",
    "OTROHERIDO",
    "NEMUERTO",
    "NEHERIDO",
    "CLASACC",
    "ESTATUS",
]

COLUMN_RENAMES = {
    "COBERTURA": "cobertura",
    "ID_ENTIDAD": "id_entidad",
    "ID_MUNICIPIO": "id_municipio",
    "ANIO": "anio",
    "MES": "mes",
    "ID_HORA": "hora",
    "ID_MINUTO": "minuto",
    "ID_DIA": "dia",
    "DIASEMANA": "dia_semana",
    "URBANA": "urbana",
    "SUBURBANA": "suburbana",
    "TIPACCID": "tipo_accidente",
    "AUTOMOVIL": "automovil",
    "CAMPASAJ": "camioneta_pasajeros",
    "MICROBUS": "microbus",
    "PASCAMION": "camion_pasajeros",
    "OMNIBUS": "omnibus",
    "TRANVIA": "tranvia",
    "CAMIONETA": "camioneta_carga",
    "CAMION": "camion_carga",
    "TRACTOR": "tractor",
    "FERROCARRI": "ferrocarril",
    "MOTOCICLET": "motocicleta",
    "BICICLETA": "bicicleta",
    "OTROVEHIC": "otro_vehiculo",
    "CAUSAACCI": "causa_accidente",
    "CAPAROD": "superficie_rodamiento",
    "SEXO": "sexo_conductor",
    "ALIENTO": "aliento",
    "CINTURON": "cinturon",
    "ID_EDAD": "edad_codigo",
    "CONDMUERTO": "conductores_muertos",
    "CONDHERIDO": "conductores_heridos",
    "PASAMUERTO": "pasajeros_muertos",
    "PASAHERIDO": "pasajeros_heridos",
    "PEATMUERTO": "peatones_muertos",
    "PEATHERIDO": "peatones_heridos",
    "CICLMUERTO": "ciclistas_muertos",
    "CICLHERIDO": "ciclistas_heridos",
    "OTROMUERTO": "otros_muertos",
    "OTROHERIDO": "otros_heridos",
    "NEMUERTO": "no_especificados_muertos",
    "NEHERIDO": "no_especificados_heridos",
    "CLASACC": "clasificacion_accidente",
    "ESTATUS": "estatus",
}

VEHICLE_COLUMNS = [
    "automovil",
    "camioneta_pasajeros",
    "microbus",
    "camion_pasajeros",
    "omnibus",
    "tranvia",
    "camioneta_carga",
    "camion_carga",
    "tractor",
    "ferrocarril",
    "motocicleta",
    "bicicleta",
    "otro_vehiculo",
]

DEATH_COLUMNS = [
    "conductores_muertos",
    "pasajeros_muertos",
    "peatones_muertos",
    "ciclistas_muertos",
    "otros_muertos",
    "no_especificados_muertos",
]

INJURY_COLUMNS = [
    "conductores_heridos",
    "pasajeros_heridos",
    "peatones_heridos",
    "ciclistas_heridos",
    "otros_heridos",
    "no_especificados_heridos",
]

NUMERIC_COLUMNS = [
    "anio",
    "mes",
    "hora",
    "minuto",
    "dia",
    "edad_codigo",
    *VEHICLE_COLUMNS,
    *DEATH_COLUMNS,
    *INJURY_COLUMNS,
]

OUTPUT_COLUMNS = [
    "anio",
    "mes",
    "dia",
    "fecha",
    "hora",
    "minuto",
    "hora_minuto",
    "dia_semana",
    "id_entidad",
    "entidad",
    "id_municipio",
    "municipio",
    "cve_municipio",
    "cobertura",
    "zona",
    "urbana",
    "suburbana",
    "tipo_accidente",
    "causa_accidente",
    "clasificacion_accidente",
    "superficie_rodamiento",
    "sexo_conductor",
    "aliento",
    "cinturon",
    "edad_codigo",
    "edad_conductor",
    *VEHICLE_COLUMNS,
    "total_vehiculos",
    *DEATH_COLUMNS,
    *INJURY_COLUMNS,
    "victimas_muertas",
    "victimas_heridas",
    "total_victimas",
    "hay_muertos",
    "hay_heridos",
    "accidente_con_victimas",
    "accidente_grave",
    "es_certificado_cero",
    "estatus",
    "fuente_archivo",
    "worker_node",
]

SUMMARY_METRICS = [
    "accidentes",
    "accidentes_con_heridos",
    "accidentes_con_muertos",
    "victimas_heridas",
    "victimas_muertas",
    "total_victimas",
    "indice_gravedad",
]


@dataclass(frozen=True)
class NodeShard:
    """Logical worker node assignment."""

    name: str
    state_ids: tuple[str, ...]
    description: str


@dataclass(frozen=True)
class PipelineOptions:
    raw_dir: Path
    output_dir: Path
    years: tuple[int, ...] | None
    engine: str
    chunksize: int
    max_rows_per_file: int | None
    write_csv: bool
    write_parquet: bool
    ray_address: str | None

