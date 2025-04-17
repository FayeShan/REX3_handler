"""Command‑line interface exposed as `rex3` script."""
from __future__ import annotations

import argparse
import logging
from pathlib import Path

from .downloader import download_files
from .extractor import unzip_dir
from .converter import convert_years_to_zarr

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def _parse() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="REX3 Toolkit – download and process MRIO data")
    sub = p.add_subparsers(dest="cmd", required=True)

    # download
    dl = sub.add_parser("download", help="Download raw ZIPs from Zenodo")
    dl.add_argument("mode", choices=["all", "single", "range"], help="Selection mode")
    dl.add_argument("--year", type=int, help="Year if mode=single")
    dl.add_argument("--start", type=int, help="Start year if mode=range")
    dl.add_argument("--end", type=int, help="End year if mode=range")
    dl.add_argument("--workers", type=int, default=4)
    dl.add_argument("--out", default="downloads")

    # unzip
    uz = sub.add_parser("extract", help="Unzip previously downloaded archives")
    uz.add_argument("--zip-dir", default="downloads")
    uz.add_argument("--out", default="unzipped")

    # convert
    cv = sub.add_parser("convert", help="Convert extracted .mat files to Zarr")
    cv.add_argument("--years", nargs="*", type=int, metavar="YEAR", help="Subset of years, default all")
    cv.add_argument("--mat-root", default="unzipped")
    cv.add_argument("--out", default="REX3ZARR")
    cv.add_argument("--overwrite", action="store_true")

    return p.parse_args()


def main() -> None:  
    ns = _parse()

    if ns.cmd == "download":
        yr_range = (ns.start, ns.end) if ns.mode == "range" else None
        download_files(
            mode=ns.mode,
            year=ns.year,
            year_range=yr_range,
            max_workers=ns.workers,
            out_dir=ns.out,
        )
    elif ns.cmd == "extract":
        unzip_dir(ns.zip_dir, ns.out)
    elif ns.cmd == "convert":
        convert_years_to_zarr(ns.years, extracted_root=ns.mat_root, zarr_root=ns.out, overwrite=ns.overwrite)


if __name__ == "__main__":  
    main()