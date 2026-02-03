"""I/O utilities for FEC data processing."""

from pathlib import Path
from typing import overload, Literal

import polars as pl


# Standard Polars read parameters for FEC data
FEC_READ_PARAMS = {
    "infer_schema_length": 10000,
    "ignore_errors": True,
    "encoding": "utf8-lossy",
}


def atomic_write_csv(
    df: pl.DataFrame,
    output_path: Path,
    backup: bool = False,
) -> None:
    """Write CSV atomically using temp file + rename pattern.

    This ensures that the output file is never in a partial state.
    If the write fails, the original file remains intact.

    Args:
        df: DataFrame to write
        output_path: Path to the output file
        backup: If True and output exists, rename to .csv.bak first
    """
    if backup and output_path.exists():
        backup_path = output_path.with_suffix(".csv.bak")
        output_path.rename(backup_path)

    temp_path = output_path.with_suffix(".csv.tmp")
    df.write_csv(temp_path)
    temp_path.rename(output_path)


@overload
def read_fec_csv(
    path: Path,
    columns: list[str] | None = None,
    lazy: Literal[False] = False,
) -> pl.DataFrame: ...


@overload
def read_fec_csv(
    path: Path,
    columns: list[str] | None = None,
    lazy: Literal[True] = True,
) -> pl.LazyFrame: ...


def read_fec_csv(
    path: Path,
    columns: list[str] | None = None,
    lazy: bool = False,
) -> pl.DataFrame | pl.LazyFrame:
    """Read a CSV file with standardized FEC parameters.

    Uses consistent parameters across all FEC data processing:
    - infer_schema_length=10000 (handle varying data types)
    - ignore_errors=True (skip malformed rows)
    - encoding="utf8-lossy" (handle encoding issues)

    Args:
        path: Path to the CSV file
        columns: List of column names to read (None for all)
        lazy: If True, return LazyFrame for memory efficiency

    Returns:
        DataFrame or LazyFrame with the CSV contents
    """
    if lazy:
        return pl.scan_csv(
            path,
            **FEC_READ_PARAMS,
        )
    else:
        return pl.read_csv(
            path,
            columns=columns,
            **FEC_READ_PARAMS,
        )


@overload
def read_fec_pipe_delimited(
    path: Path,
    columns: list[str],
    lazy: Literal[False] = False,
) -> pl.DataFrame: ...


@overload
def read_fec_pipe_delimited(
    path: Path,
    columns: list[str],
    lazy: Literal[True] = True,
) -> pl.LazyFrame: ...


def read_fec_pipe_delimited(
    path: Path,
    columns: list[str],
    lazy: bool = False,
) -> pl.DataFrame | pl.LazyFrame:
    """Read a pipe-delimited FEC bulk data file.

    FEC bulk data files are pipe-delimited without headers.
    This function reads them with consistent parameters.

    Args:
        path: Path to the pipe-delimited file
        columns: List of column names (required since files have no header)
        lazy: If True, return LazyFrame for memory efficiency

    Returns:
        DataFrame or LazyFrame with the file contents
    """
    params = {
        "separator": "|",
        "has_header": False,
        "new_columns": columns,
        "quote_char": None,
        "truncate_ragged_lines": True,
        **FEC_READ_PARAMS,
    }

    if lazy:
        return pl.scan_csv(path, **params)
    else:
        return pl.read_csv(path, **params)
