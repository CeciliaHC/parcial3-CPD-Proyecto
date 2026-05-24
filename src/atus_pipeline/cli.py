"""Command line interface for the ATUS Ray pipeline."""

from __future__ import annotations

import argparse
from pathlib import Path

from .config import PipelineOptions
from .pipeline import run_pipeline


def _parse_years(values: list[str] | None) -> tuple[int, ...] | None:
    if not values:
        return None
    years: list[int] = []
    for value in values:
        if "-" in value:
            start, end = value.split("-", 1)
            years.extend(range(int(start), int(end) + 1))
        else:
            years.append(int(value))
    return tuple(sorted(set(years)))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Limpieza distribuida de datos ATUS con Python, Pandas y Ray."
    )
    parser.add_argument(
        "--raw-dir",
        type=Path,
        default=Path("conjunto_de_datos_atus_anual_csv"),
        help="Carpeta raiz descargada desde INEGI.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/processed"),
        help="Carpeta de salida para datos limpios y resumenes.",
    )
    parser.add_argument(
        "--years",
        nargs="*",
        help="Anios a procesar. Acepta valores como 2024 o rangos como 2022-2024.",
    )
    parser.add_argument(
        "--engine",
        choices=["ray", "local"],
        default="ray",
        help="ray usa workers remotos; local sirve como linea base secuencial.",
    )
    parser.add_argument(
        "--chunksize",
        type=int,
        default=100_000,
        help="Filas por bloque Pandas dentro de cada worker.",
    )
    parser.add_argument(
        "--max-rows-per-file",
        type=int,
        default=None,
        help="Limite opcional para pruebas rapidas sin procesar archivos completos.",
    )
    parser.add_argument(
        "--no-csv",
        action="store_true",
        help="No escribir particiones CSV limpias.",
    )
    parser.add_argument(
        "--write-parquet",
        action="store_true",
        help="Escribir particiones Parquet ademas de CSV. Requiere pyarrow.",
    )
    parser.add_argument(
        "--ray-address",
        default=None,
        help="Direccion de Ray Cluster. Usa 'auto' al correr contra un head node.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    options = PipelineOptions(
        raw_dir=args.raw_dir,
        output_dir=args.output_dir,
        years=_parse_years(args.years),
        engine=args.engine,
        chunksize=args.chunksize,
        max_rows_per_file=args.max_rows_per_file,
        write_csv=not args.no_csv,
        write_parquet=args.write_parquet,
        ray_address=args.ray_address,
    )
    result = run_pipeline(options)
    print("Pipeline terminado")
    print(f"Salida: {result['output_dir']}")
    print(f"Resumenes: {result['summary_dir']}")
    print(f"Filas limpias: {result['total_rows_cleaned']}")
    print(f"Tiempo total: {result['total_elapsed_seconds']} segundos")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

