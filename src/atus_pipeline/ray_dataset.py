"""Ray Data helpers for downstream analysis and dashboard work."""

from __future__ import annotations

from pathlib import Path


def load_clean_dataset(processed_dir: str | Path = "data/processed"):
    """Load cleaned partitions as a Ray Data Dataset.

    Parquet is preferred when available. Otherwise, CSV clean partitions are used.
    This helper is intended for the analysis/dashboard stage.
    """

    import ray.data as rd

    processed_path = Path(processed_dir)
    parquet_files = sorted((processed_path / "clean_parquet").glob("**/*.parquet"))
    if parquet_files:
        return rd.read_parquet([str(path) for path in parquet_files])

    csv_files = sorted((processed_path / "clean_csv").glob("**/*.csv"))
    if csv_files:
        return rd.read_csv([str(path) for path in csv_files])

    raise FileNotFoundError(
        f"No se encontraron particiones limpias en {processed_path}"
    )

