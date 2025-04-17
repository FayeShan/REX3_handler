"""Download files from ZENODO."""
from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Iterable

import requests
from tqdm import tqdm

from .constants import BASE_URL, ALL_FILES

_CHUNK = 8192  # 8 KiB


def _download_one(file_name: str, dest: Path) -> str:
    """Download `file_name` into `dest` and return a status string."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    url = f"{BASE_URL}/{file_name}?download=1"

    try:
        with requests.get(url, stream=True, timeout=60) as r:
            r.raise_for_status()
            total = int(r.headers.get("content-length", 0))
            with open(dest, "wb") as fh, tqdm(
                total=total,
                unit="B",
                unit_scale=True,
                unit_divisor=1024,
                desc=file_name,
                leave=False,
            ) as bar:
                for chunk in r.iter_content(chunk_size=_CHUNK):
                    if chunk:
                        fh.write(chunk)
                        bar.update(len(chunk))
        return f"Successed {file_name}"
    except Exception as exc:  # pragma: no cover
        return f"Failed {file_name} – {exc}"


def _resolve_selection(mode: str, year: int | None, year_range: tuple[int, int] | None) -> list[str]:
    if mode == "all":
        return sorted(ALL_FILES)
    if mode == "single":
        if year is None:
            raise ValueError("year must be given when mode='single'")
        return [f"REX3_{year}.zip"]
    if mode == "range":
        if not year_range or len(year_range) != 2:
            raise ValueError("year_range=(start,end) must be supplied when mode='range'")
        a, b = year_range
        return [f"REX3_{y}.zip" for y in range(a, b + 1)]
    raise ValueError("mode must be one of 'all'|'single'|'range'")


def download_files(
    mode: str = "all",
    *,
    year: int | None = None,
    year_range: tuple[int, int] | None = None,
    max_workers: int = 4,
    out_dir: str | os.PathLike = "downloads",
) -> None:
    """Public API – download a selection of REX3 ZIPs.

    Parameters
    ----------
    mode        'all', 'single', or 'range'.
    year        required if *mode* == 'single'.
    year_range  (start, end) inclusive if *mode* == 'range'.
    max_workers threads (I/O bound → threads faster than processes).
    out_dir     destination directory (created if absent).
    """
    files = _resolve_selection(mode, year, year_range)
    out = Path(out_dir)

    print(f" Downloading {len(files)} file(s) to '{out.resolve()}' using {max_workers} threads…")

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(_download_one, f, out / f): f for f in files}
        for fut in as_completed(futures):
            print(fut.result())