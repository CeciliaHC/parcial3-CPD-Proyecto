"""Cleaning rules for the INEGI ATUS annual CSV files."""

from __future__ import annotations

from pathlib import Path

from .config import (
    COLUMN_RENAMES,
    DEATH_COLUMNS,
    INJURY_COLUMNS,
    NUMERIC_COLUMNS,
    OUTPUT_COLUMNS,
    RAW_COLUMNS,
    SUMMARY_METRICS,
    VEHICLE_COLUMNS,
)


def _clean_text(series):
    import pandas as pd

    cleaned = (
        series.astype("string")
        .str.replace("\ufeff", "", regex=False)
        .str.replace("\t", "", regex=False)
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
    )
    return cleaned.replace({"": pd.NA})


def _to_int(series):
    import pandas as pd

    return pd.to_numeric(_clean_text(series), errors="coerce").astype("Int64")


def _pad_code(series, width: int):
    import pandas as pd

    cleaned = _clean_text(series).str.replace(r"\.0$", "", regex=True)
    cleaned = cleaned.where(cleaned.notna(), pd.NA)
    return cleaned.str.zfill(width)


def _safe_sum(df, columns: list[str]):
    return df[columns].fillna(0).sum(axis=1).astype("Int64")


def _derive_zone(df):
    import pandas as pd

    urbana = df["urbana"].fillna("")
    suburbana = df["suburbana"].fillna("")
    zona = pd.Series("No especificada", index=df.index, dtype="string")

    zona = zona.mask(
        urbana.str.contains("Accidente", case=False, na=False)
        & ~urbana.str.contains("Sin accidente", case=False, na=False),
        "Urbana",
    )
    zona = zona.mask(
        suburbana.str.contains("Accidente", case=False, na=False)
        & ~suburbana.str.contains("Sin accidente", case=False, na=False),
        "Suburbana",
    )
    zona = zona.mask(df["es_certificado_cero"], "Certificado cero")
    return zona


def _derive_date(df):
    import pandas as pd

    valid_day = df["dia"].between(1, 31)
    valid_month = df["mes"].between(1, 12)
    date_parts = pd.DataFrame(
        {
            "year": df["anio"],
            "month": df["mes"].where(valid_month),
            "day": df["dia"].where(valid_day),
        }
    )
    return pd.to_datetime(date_parts, errors="coerce").dt.strftime("%Y-%m-%d")


def clean_dataframe(df, catalogs: dict, source_file: str | None, worker_node: str):
    """Normalize one Pandas batch from ATUS."""

    import pandas as pd

    df = df.copy()
    df.columns = [str(column).strip().upper() for column in df.columns]

    for column in RAW_COLUMNS:
        if column not in df.columns:
            df[column] = pd.NA

    df = df[RAW_COLUMNS].rename(columns=COLUMN_RENAMES)

    for column in df.columns:
        if column not in NUMERIC_COLUMNS:
            df[column] = _clean_text(df[column])

    df["id_entidad"] = _pad_code(df["id_entidad"], 2)
    df["id_municipio"] = _pad_code(df["id_municipio"], 3)
    df["cve_municipio"] = df["id_entidad"] + df["id_municipio"]

    for column in NUMERIC_COLUMNS:
        df[column] = _to_int(df[column])

    df["hora"] = df["hora"].where(df["hora"].between(0, 23))
    df["minuto"] = df["minuto"].where(df["minuto"].between(0, 59))
    df["dia"] = df["dia"].where(df["dia"].between(1, 31))
    df["edad_conductor"] = df["edad_codigo"].where(df["edad_codigo"].between(12, 98))

    df["fecha"] = _derive_date(df)
    valid_time = df["hora"].notna() & df["minuto"].notna()
    hour = df["hora"].astype("string").str.zfill(2)
    minute = df["minuto"].astype("string").str.zfill(2)
    df["hora_minuto"] = (hour + ":" + minute).where(valid_time)

    for column in VEHICLE_COLUMNS + DEATH_COLUMNS + INJURY_COLUMNS:
        df[column] = df[column].fillna(0).astype("Int64")

    df["victimas_muertas"] = _safe_sum(df, DEATH_COLUMNS)
    df["victimas_heridas"] = _safe_sum(df, INJURY_COLUMNS)
    df["total_victimas"] = df["victimas_muertas"] + df["victimas_heridas"]
    df["total_vehiculos"] = _safe_sum(df, VEHICLE_COLUMNS)

    certificado_cols = [
        "tipo_accidente",
        "causa_accidente",
        "clasificacion_accidente",
    ]
    df["es_certificado_cero"] = False
    for column in certificado_cols:
        df["es_certificado_cero"] = df["es_certificado_cero"] | df[column].str.contains(
            "Certificado cero", case=False, na=False
        )

    df["zona"] = _derive_zone(df)
    df["hay_muertos"] = df["victimas_muertas"] > 0
    df["hay_heridos"] = df["victimas_heridas"] > 0
    df["accidente_con_victimas"] = df["total_victimas"] > 0
    df["accidente_grave"] = df["hay_muertos"] | (
        df["clasificacion_accidente"].str.contains("Fatal", case=False, na=False)
    )

    entidades = catalogs["entidades"][["id_entidad", "entidad"]]
    municipios = catalogs["municipios"][["id_entidad", "id_municipio", "municipio"]]
    df = df.merge(entidades, on="id_entidad", how="left")
    df = df.merge(municipios, on=["id_entidad", "id_municipio"], how="left")

    df["fuente_archivo"] = Path(source_file).name if source_file else pd.NA
    df["worker_node"] = worker_node

    for column in OUTPUT_COLUMNS:
        if column not in df.columns:
            df[column] = pd.NA

    return df[OUTPUT_COLUMNS]


def accident_rows(df):
    """Rows that count as accidents for analytical summaries."""

    return df[~df["es_certificado_cero"].fillna(False)].copy()


def aggregate_dataframe(df, group_columns: list[str]):
    import pandas as pd

    metrics = list(SUMMARY_METRICS)
    if df.empty:
        return pd.DataFrame(columns=[*group_columns, *metrics])

    grouped = (
        df.groupby(group_columns, dropna=False)
        .agg(
            accidentes=("anio", "size"),
            accidentes_con_heridos=("hay_heridos", "sum"),
            accidentes_con_muertos=("hay_muertos", "sum"),
            victimas_heridas=("victimas_heridas", "sum"),
            victimas_muertas=("victimas_muertas", "sum"),
            total_victimas=("total_victimas", "sum"),
        )
        .reset_index()
    )
    grouped["indice_gravedad"] = (
        (grouped["victimas_heridas"] + grouped["victimas_muertas"] * 5)
        / grouped["accidentes"].where(grouped["accidentes"] != 0, 1)
    ).round(6)
    return grouped[[*group_columns, *metrics]]


def make_summaries(cleaned):
    df = accident_rows(cleaned)
    return {
        "accidents_by_state": aggregate_dataframe(df, ["id_entidad", "entidad"]),
        "accidents_by_municipality": aggregate_dataframe(
            df, ["id_entidad", "entidad", "id_municipio", "municipio"]
        ),
        "accidents_by_hour": aggregate_dataframe(df, ["hora"]),
        "accidents_by_month": aggregate_dataframe(df, ["anio", "mes"]),
        "accidents_by_cause": aggregate_dataframe(df, ["causa_accidente"]),
        "accidents_by_type": aggregate_dataframe(df, ["tipo_accidente"]),
        "accidents_by_classification": aggregate_dataframe(
            df, ["clasificacion_accidente"]
        ),
        "annual_trend": aggregate_dataframe(df, ["anio"]),
    }

