"""Convert extracted MATLAB .mat files into yearly Zarr stores."""
from __future__ import annotations

import gc
import logging
import os
from pathlib import Path

import h5py
import numpy as np
import xarray as xr

__all__ = ["convert_years_to_zarr"]
log = logging.getLogger(__name__)

# constant dimensions
_NR, _NS, _N_IND, _N_REG = 189, 163, 19, 189


def _load_mat_v73(fname: os.PathLike) -> dict:
    """Read MATLAB v7.3 file into nested dict of NumPy arrays/objects."""

    def _get(hobj, key):
        item = hobj[key]
        if isinstance(item, h5py.Dataset):
            data = item[()]
            # decode MATLAB utf‑16 object strings lazily
            if item.dtype.kind == "O":
                data = np.array(
                    [hobj[ref][:].tobytes().decode("utf-16le").rstrip("\x00") for ref in data.flat],
                    dtype=object,
                ).reshape(data.shape)
            return data
        if isinstance(item, h5py.Group):
            return {k: _get(item, k) for k in item.keys()}
        return None

    with h5py.File(fname, "r") as f:
        return {k: _get(f, k) for k in f.keys()}


def _build_dataset(year_dir: Path) -> xr.Dataset:
    # read matrices
    T = np.transpose(_load_mat_v73(year_dir / "T_REX3.mat")["T_REX3"], (1, 0)).astype("float32")
    Y = np.transpose(_load_mat_v73(year_dir / "Y_REX3.mat")["Y_REX3"], (1, 0)).astype("float32")
    Q = np.transpose(_load_mat_v73(year_dir / "Q_REX3.mat")["Q_REX3"], (1, 0)).astype("float32")
    QY = np.transpose(_load_mat_v73(year_dir / "Q_Y_REX3.mat")["Q_Y_REX3"], (1, 0)).astype("float32")

    ds = xr.Dataset()
    ds["T"] = xr.DataArray(
        T.reshape((_NR, _NS, _NR, _NS)),
        dims=["output_region", "output_sector", "input_region", "input_sector"],
    )
    ds["Y"] = xr.DataArray(
        Y.reshape((_NR, _NS, _N_REG)),
        dims=["output_region", "output_sector", "input_region"],
    )
    ds["Q"] = xr.DataArray(
        Q.reshape((_N_IND, _NR, _NS)),
        dims=["environmental_indicator", "input_region", "input_sector"],
    )
    ds["Q_Y"] = xr.DataArray(
        QY,
        dims=["environmental_indicator", "input_region"],
    )
    return ds


def convert_years_to_zarr(
    years: Iterable[int] | None = None,
    *,
    extracted_root: str | os.PathLike = "unzipped",
    zarr_root: str | os.PathLike = "REX3ZARR",
    overwrite: bool = False,
) -> None:
    """Convert selected years (default = all *present* in *extracted_root*) to Zarr.

    If *years* is **None** we first scan *extracted_root* for folders that look
    like `REX3_<YYYY>` and build the list automatically. That way you can
    download / extract a single year (or an arbitrary subset) and run

    ```bash
    rex3 convert  # no --years needed
    ```

    and only the data you actually have will be converted.
    """
    extracted_root = Path(extracted_root)
    zarr_root = Path(zarr_root)
    zarr_root.mkdir(exist_ok=True, parents=True)

    if years is None:
        years = sorted(
            int(p.name.split("_", 1)[1])
            for p in extracted_root.glob("REX3_????")
            if p.is_dir() and p.name.split("_", 1)[1].isdigit()
        )
        if not years:
            logging.warning("No REX3_* folders found in %s — nothing to convert", extracted_root)
            return

    for yr in years:
        logging.info("Processing %d", yr)
        year_dir = extracted_root / f"REX3_{yr}"
        if not year_dir.exists():
            logging.warning("✗ Skipping %s – not found", year_dir.name)
            continue

        ds = _build_dataset(year_dir)
        dest = zarr_root / f"{yr}.zarr"
        mode = "w" if overwrite else ("w-" if not dest.exists() else "r+")
        ds.to_zarr(dest, mode=mode, encoding={"T": {"chunks": (47, 41, 47, 41)}}, consolidated=True)
        del ds
        gc.collect()
        logging.info(" Saved %s", dest)