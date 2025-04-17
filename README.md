# REX3handler
 

Python helper to **download, extract, and convert** the [REX3 MRIO dataset](https://zenodo.org/records/10354283) into chunked **Zarr** stores so you can open each year instantly with `xarray`.

## Quick‑start

```bash
pip install rex3handler  # once published

# 1⃣  Download the **entire archive** (all years + misc.) using 8 threads
rex3 download all --workers 8

# 2⃣  Download a **single year** (2005) using 4 threads
rex3 download single --year 2005 --workers 4

# 3⃣  Download a **range of years** (1999–2004) using 8 threads
rex3 download range --start 1999 --end 2004 --workers 8

# Unzip everything
rex3 extract

# Convert all extracted years to Zarr (≈ 12 GB output)
rex3 convert

# Open a year in Python
import xarray as xr
ds = xr.open_zarr("REX3ZARR/2002.zarr", consolidated=True)
print(ds)