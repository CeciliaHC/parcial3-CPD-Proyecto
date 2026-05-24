"""Catalog loading and worker-node partitioning helpers."""

from __future__ import annotations

import unicodedata
from pathlib import Path

from .config import CATALOG_SUBDIR, NodeShard


def _ascii_key(value: str) -> str:
    text = unicodedata.normalize("NFKD", value or "")
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return text.upper().strip()


def _read_catalog(path: Path):
    import pandas as pd

    df = pd.read_csv(path, dtype=str, encoding="utf-8")
    df.columns = [col.strip().upper() for col in df.columns]
    for column in df.columns:
        df[column] = df[column].astype("string").str.strip()
    return df


def load_catalogs(raw_dir: Path) -> dict:
    """Load INEGI catalogs used to enrich ATUS records."""

    catalog_dir = raw_dir / CATALOG_SUBDIR

    entidades = _read_catalog(catalog_dir / "tc_entidad.csv")
    entidades = entidades.rename(
        columns={"ID_ENTIDAD": "id_entidad", "NOM_ENTIDAD": "entidad"}
    )
    entidades["id_entidad"] = entidades["id_entidad"].str.zfill(2)

    municipios = _read_catalog(catalog_dir / "tc_municipio.csv")
    municipios = municipios.rename(
        columns={
            "ID_ENTIDAD": "id_entidad",
            "ID_MUNICIPIO": "id_municipio",
            "NOM_MUNICIPIO": "municipio",
        }
    )
    municipios["id_entidad"] = municipios["id_entidad"].str.zfill(2)
    municipios["id_municipio"] = municipios["id_municipio"].str.zfill(3)

    meses = _read_catalog(catalog_dir / "tc_periodo_mes.csv").rename(
        columns={"MES": "mes", "DESCRIPCION_MES": "mes_nombre"}
    )
    edades = _read_catalog(catalog_dir / "tc_edad.csv").rename(
        columns={"ID_EDAD": "edad_codigo", "DESC_EDAD": "edad_descripcion"}
    )

    return {
        "entidades": entidades,
        "municipios": municipios,
        "meses": meses,
        "edades": edades,
    }


def build_state_node_shards(entidades) -> list[NodeShard]:
    """Create the A-C, D-M and N-Z logical nodes shown in the PDF diagram."""

    groups = {
        "worker_node_1_a_c": {"letters": tuple("ABC"), "ids": []},
        "worker_node_2_d_m": {"letters": tuple("DEFGHIJKLM"), "ids": []},
        "worker_node_3_n_z": {"letters": tuple("NOPQRSTUVWXYZ"), "ids": []},
    }

    for row in entidades[["id_entidad", "entidad"]].itertuples(index=False):
        first_letter = _ascii_key(row.entidad)[:1]
        for group in groups.values():
            if first_letter in group["letters"]:
                group["ids"].append(str(row.id_entidad).zfill(2))
                break

    return [
        NodeShard(
            name="worker_node_1_a_c",
            state_ids=tuple(groups["worker_node_1_a_c"]["ids"]),
            description="Estados A-C segun nombre de entidad",
        ),
        NodeShard(
            name="worker_node_2_d_m",
            state_ids=tuple(groups["worker_node_2_d_m"]["ids"]),
            description="Estados D-M segun nombre de entidad",
        ),
        NodeShard(
            name="worker_node_3_n_z",
            state_ids=tuple(groups["worker_node_3_n_z"]["ids"]),
            description="Estados N-Z segun nombre de entidad",
        ),
    ]

