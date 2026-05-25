"""Distributed ATUS cleaning pipeline with Ray Core and Pandas."""

from __future__ import annotations

import time
import shutil
from pathlib import Path

from .catalogs import build_state_node_shards, load_catalogs
from .cleaning import clean_dataframe, make_summaries
from .config import PipelineOptions, RAW_DATA_SUBDIR, SUMMARY_METRICS


def discover_atus_files(raw_dir: Path, years: tuple[int, ...] | None) -> list[Path]:
    data_dir = raw_dir / RAW_DATA_SUBDIR
    files = sorted(data_dir.glob("atus_anual_*.csv"))
    if years:
        allowed = {int(year) for year in years}
        files = [
            file
            for file in files
            if _year_from_file(file) is not None and _year_from_file(file) in allowed
        ]
    return files


def _year_from_file(path: Path) -> int | None:
    try:
        return int(path.stem.rsplit("_", 1)[-1])
    except ValueError:
        return None


def _append_csv(df, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    write_header = not path.exists()
    df.to_csv(path, index=False, encoding="utf-8", mode="a", header=write_header)


def _write_parquet(df, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)


def _prepare_output_dir(output_dir: Path):
    for subdir in ("clean_csv", "clean_parquet", "summary"):
        target = output_dir / subdir
        if target.exists():
            shutil.rmtree(target)


def _process_shard(
    shard_payload: dict,
    files: list[str],
    catalogs: dict,
    output_dir: str,
    chunksize: int,
    max_rows_per_file: int | None,
    write_csv: bool,
    write_parquet: bool,
) -> dict:
    import pandas as pd

    started = time.perf_counter()
    shard_name = shard_payload["name"]
    state_ids = set(shard_payload["state_ids"])
    out_dir = Path(output_dir)

    summaries: dict[str, list] = {}
    quality_rows = []
    rows_read = 0
    rows_selected = 0
    rows_cleaned = 0
    parquet_part = 0

    for file_name in files:
        file_path = Path(file_name)
        file_started = time.perf_counter()
        file_rows_read = 0
        file_rows_selected = 0
        file_rows_cleaned = 0
        file_cert_zero = 0
        file_invalid_date = 0
        file_invalid_hour = 0
        year = _year_from_file(file_path)

        reader = pd.read_csv(
            file_path,
            dtype=str,
            encoding="utf-8",
            chunksize=chunksize,
            nrows=max_rows_per_file,
            low_memory=False,
        )

        for chunk in reader:
            file_rows_read += len(chunk)
            rows_read += len(chunk)

            chunk.columns = [str(column).strip().upper() for column in chunk.columns]
            if "ID_ENTIDAD" not in chunk.columns:
                continue
            entity_ids = (
                chunk["ID_ENTIDAD"]
                .astype("string")
                .str.replace("\t", "", regex=False)
                .str.strip()
                .str.zfill(2)
            )
            chunk = chunk.loc[entity_ids.isin(state_ids)].copy()
            if chunk.empty:
                continue

            file_rows_selected += len(chunk)
            rows_selected += len(chunk)

            cleaned = clean_dataframe(
                chunk,
                catalogs=catalogs,
                source_file=str(file_path),
                worker_node=shard_name,
            )
            file_rows_cleaned += len(cleaned)
            rows_cleaned += len(cleaned)
            file_cert_zero += int(cleaned["es_certificado_cero"].sum())
            file_invalid_date += int(cleaned["fecha"].isna().sum())
            file_invalid_hour += int(cleaned["hora"].isna().sum())

            if write_csv:
                clean_path = (
                    out_dir
                    / "clean_csv"
                    / shard_name
                    / f"atus_clean_{year}_{shard_name}.csv"
                )
                _append_csv(cleaned, clean_path)

            if write_parquet:
                parquet_part += 1
                parquet_path = (
                    out_dir
                    / "clean_parquet"
                    / shard_name
                    / f"atus_clean_{year}_{shard_name}_part_{parquet_part:05d}.parquet"
                )
                _write_parquet(cleaned, parquet_path)

            for name, summary in make_summaries(cleaned).items():
                summaries.setdefault(name, []).append(summary)

        quality_rows.append(
            {
                "worker_node": shard_name,
                "fuente_archivo": file_path.name,
                "año": year,
                "rows_read": file_rows_read,
                "rows_selected_for_node": file_rows_selected,
                "rows_cleaned": file_rows_cleaned,
                "certificado_cero_rows": file_cert_zero,
                "invalid_fecha_rows": file_invalid_date,
                "invalid_hora_rows": file_invalid_hour,
                "elapsed_seconds": round(time.perf_counter() - file_started, 6),
            }
        )

    compact_summaries = {}
    for name, frames in summaries.items():
        compact_summaries[name] = _combine_summary_frames(frames)

    return {
        "worker_node": shard_name,
        "rows_read": rows_read,
        "rows_selected_for_node": rows_selected,
        "rows_cleaned": rows_cleaned,
        "elapsed_seconds": round(time.perf_counter() - started, 6),
        "summaries": compact_summaries,
        "quality_rows": quality_rows,
    }


def _combine_summary_frames(frames):
    import pandas as pd

    if not frames:
        return pd.DataFrame()
    combined = pd.concat(frames, ignore_index=True)
    group_cols = [col for col in combined.columns if col not in SUMMARY_METRICS]
    if combined.empty:
        return combined
    reduced = (
        combined.groupby(group_cols, dropna=False)
        .agg(
            accidentes=("accidentes", "sum"),
            accidentes_con_heridos=("accidentes_con_heridos", "sum"),
            accidentes_con_muertos=("accidentes_con_muertos", "sum"),
            victimas_heridas=("victimas_heridas", "sum"),
            victimas_muertas=("victimas_muertas", "sum"),
            total_victimas=("total_victimas", "sum"),
        )
        .reset_index()
    )
    reduced["indice_gravedad"] = (
        (reduced["victimas_heridas"] + reduced["victimas_muertas"] * 5)
        / reduced["accidentes"].where(reduced["accidentes"] != 0, 1)
    ).round(6)
    return reduced[[*group_cols, *SUMMARY_METRICS]]


def _write_head_outputs(results: list[dict], options: PipelineOptions, started: float):
    import pandas as pd

    options.output_dir.mkdir(parents=True, exist_ok=True)
    summary_dir = options.output_dir / "summary"
    summary_dir.mkdir(parents=True, exist_ok=True)

    summary_names = sorted(
        {
            name
            for result in results
            for name in result.get("summaries", {}).keys()
        }
    )
    for name in summary_names:
        frames = [
            result["summaries"][name]
            for result in results
            if name in result.get("summaries", {})
        ]
        summary = _combine_summary_frames(frames)
        summary.to_csv(summary_dir / f"{name}.csv", index=False, encoding="utf-8")

    quality = pd.DataFrame(
        row for result in results for row in result.get("quality_rows", [])
    )
    quality.to_csv(summary_dir / "data_quality_report.csv", index=False, encoding="utf-8")

    worker_metrics = pd.DataFrame(
        {
            "worker_node": result["worker_node"],
            "rows_read": result["rows_read"],
            "rows_selected_for_node": result["rows_selected_for_node"],
            "rows_cleaned": result["rows_cleaned"],
            "elapsed_seconds": result["elapsed_seconds"],
        }
        for result in results
    )
    total_elapsed = round(time.perf_counter() - started, 6)
    worker_metrics["engine"] = options.engine
    worker_metrics["total_pipeline_seconds"] = total_elapsed
    worker_metrics["rows_per_second"] = (
        worker_metrics["rows_cleaned"]
        / worker_metrics["elapsed_seconds"].where(worker_metrics["elapsed_seconds"] != 0, 1)
    ).round(3)
    worker_metrics.to_csv(summary_dir / "run_metrics.csv", index=False, encoding="utf-8")

    return {
        "output_dir": str(options.output_dir),
        "summary_dir": str(summary_dir),
        "total_rows_cleaned": int(worker_metrics["rows_cleaned"].sum()),
        "total_elapsed_seconds": total_elapsed,
    }


def run_pipeline(options: PipelineOptions) -> dict:
    started = time.perf_counter()
    catalogs = load_catalogs(options.raw_dir)
    files = discover_atus_files(options.raw_dir, options.years)
    if not files:
        raise FileNotFoundError(
            f"No se encontraron archivos atus_anual_*.csv en {options.raw_dir}"
        )

    shards = build_state_node_shards(catalogs["entidades"])
    shard_payloads = [
        {
            "name": shard.name,
            "state_ids": shard.state_ids,
            "description": shard.description,
        }
        for shard in shards
    ]
    file_names = [str(path) for path in files]

    if not options.append_output:
        _prepare_output_dir(options.output_dir)

    if options.engine == "local":
        results = [
            _process_shard(
                shard_payload,
                file_names,
                catalogs,
                str(options.output_dir),
                options.chunksize,
                options.max_rows_per_file,
                options.write_csv,
                options.write_parquet,
            )
            for shard_payload in shard_payloads
        ]
    elif options.engine == "ray":
        try:
            import ray
        except ImportError as exc:
            raise RuntimeError(
                "Ray no esta instalado. Ejecuta: pip install -r requirements.txt"
            ) from exc

        init_kwargs = {"ignore_reinit_error": True}
        if options.ray_address:
            init_kwargs["address"] = options.ray_address
        ray.init(**init_kwargs)

        remote_process = ray.remote(_process_shard)
        futures = [
            remote_process.remote(
                shard_payload,
                file_names,
                catalogs,
                str(options.output_dir),
                options.chunksize,
                options.max_rows_per_file,
                options.write_csv,
                options.write_parquet,
            )
            for shard_payload in shard_payloads
        ]
        results = ray.get(futures)
    else:
        raise ValueError(f"Engine no soportado: {options.engine}")

    return _write_head_outputs(results, options, started)
