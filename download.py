import os
import requests
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

ZENODO_RECORD_ID = "10354283"
BASE_URL = f"https://zenodo.org/records/{ZENODO_RECORD_ID}/files"

ALL_FILES = {
    "matlab code to calculate MRIO results (Figure 2-5).zip",
    "matlab code to compile REX3.zip",
    "R code for regionalized BD impact assessment based on LUH2 data and maps (Figure 1).zip",
    "R code to illustrate sankeys – Figure 3–5, S10.zip",
    "REX3_Labels.zip",
}
ALL_FILES.update({f"REX3_{year}.zip" for year in range(1995, 2023)})

# Thread-safe progress bar handler
def download_file(file_name: str, save_dir: str = "downloads"):
    os.makedirs(save_dir, exist_ok=True)
    url = f"{BASE_URL}/{file_name}?download=1"
    dest_path = os.path.join(save_dir, file_name)

    try:
        with requests.get(url, stream=True, timeout=60) as r:
            r.raise_for_status()
            total_size = int(r.headers.get("content-length", 0))
            with open(dest_path, "wb") as f, tqdm(
                total=total_size,
                unit="B",
                unit_scale=True,
                unit_divisor=1024,
                desc=file_name,
                leave=False
            ) as bar:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        bar.update(len(chunk))
        return f" Finished: {file_name}"
    except Exception as e:
        return f" Failed: {file_name} — {e}"

def download_mode(mode="all", year=None, year_range=None, max_workers=4):
    if mode == "all":
        files_to_download = sorted(ALL_FILES)
    elif mode == "single":
        if year is None:
            raise ValueError("Please specify a year for single file download.")
        file_name = f"REX3_{year}.zip"
        if file_name not in ALL_FILES:
            raise ValueError(f"{file_name} not found.")
        files_to_download = [file_name]
    elif mode == "range":
        if not year_range or len(year_range) != 2:
            raise ValueError("Please provide a valid year range as a tuple (start, end).")
        start, end = year_range
        files_to_download = [f"REX3_{year}.zip" for year in range(start, end + 1)]
        for file in files_to_download:
            if file not in ALL_FILES:
                raise ValueError(f"{file} not found in available files.")
    else:
        raise ValueError("Mode must be 'all', 'single', or 'range'.")

    print(f"Starting download of {len(files_to_download)} file(s)...")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_file = {executor.submit(download_file, file): file for file in files_to_download}
        for future in as_completed(future_to_file):
            result = future.result()
            print(result)

# Example usages
# download_mode("all", max_workers=6)
# download_mode("single", year=1999, max_workers=4)
# download_mode("range", year_range=(1999, 2000), max_workers=4)

# spead for download a single file may take 

# function to unzip
import zipfile
import os



import h5py
import os
import numpy as np
import xarray as xr
import logging
import gc
 
# --- Setup logging ---
log_file = "rex3_processing.log"
logging.basicConfig(filename=log_file, level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# --- Function to read .mat file with .73 version ---
def load_mat_v73(filename):
    def get_data(obj, key):
        if isinstance(obj[key], h5py.Dataset):
            data = obj[key][()]
            if obj[key].dtype.kind == 'O':
                data = np.array([obj[ref][:].tobytes().decode('utf-16le').rstrip('\x00') for ref in data.flat], dtype=object).reshape(data.shape)
            return data
        elif isinstance(obj[key], h5py.Group):
            return {k: get_data(obj[key], k) for k in obj[key].keys()}
        else:
            return None
    with h5py.File(filename, 'r') as file:
        return {key: get_data(file, key) for key in file.keys()}

# --- Config ---
nr, ns = 189, 163
output_path = "../REX3ZARR/"
os.makedirs(output_path, exist_ok=True)

# --- Loop through years ---
for year in range(1995, 2023): # select year # can be single year, but also can be a range
    try:
        logging.info(f"Start processing year: {year}")
        datapath_data = f'/downloads/REX3_{year}/'

        # Load .mat files
        T = np.transpose(load_mat_v73(datapath_data + 'T_REX3.mat')['T_REX3'], (1, 0))
        Y_region = np.transpose(load_mat_v73(datapath_data + 'Y_REX3.mat')['Y_REX3'], (1, 0))
        Q = np.transpose(load_mat_v73(datapath_data + 'Q_REX3.mat')['Q_REX3'], (1, 0))
        Q_Y = np.transpose(load_mat_v73(datapath_data + 'Q_Y_REX3.mat')['Q_Y_REX3'], (1, 0))

        # Reshape T
        logging.info("Reshaping T...")
        T_reshaped = T.reshape((nr, ns, nr, ns)).astype('float32')

        # Create xarray Dataset
        logging.info("Creating xarray Dataset...")
        ds = xr.Dataset()
        ds["T"] = xr.DataArray(T_reshaped, dims=["output_region", "output_sector", "input_region", "input_sector"],
                               coords={"output_region": range(nr), "output_sector": range(ns),
                                       "input_region": range(nr), "input_sector": range(ns)})

        Y_reshaped = Y_region.reshape((nr, ns, 189))
        ds["Y"] = xr.DataArray(Y_reshaped, dims=["output_region", "output_sector", "input_region"],
                               coords={"output_region": range(nr), "output_sector": range(ns),
                                       "input_region": range(189)})

        Q_reshaped = Q.reshape((19, nr, ns))
        ds["Q"] = xr.DataArray(Q_reshaped, dims=["environmental_indicator", "input_region", "input_sector"],
                               coords={"environmental_indicator": range(19), "input_region": range(nr),
                                       "input_sector": range(ns)})

        ds["Q_Y"] = xr.DataArray(Q_Y, dims=["environmental_indicator", "input_region"],
                                 coords={"environmental_indicator": range(19), "input_region": range(189)})

        # Save to Zarr
        output_file = os.path.join(output_path, f"{year}.zarr")
        logging.info("Saving to Zarr...")
        ds.to_zarr(output_file, mode="w",
                   encoding={"T": {"chunks": (47, 41, 47, 41)}},
                   consolidated=True)

        logging.info(f"Finished year: {year}")

        # Clean up to free memory
        del T, Y_region, Q, Q_Y, T_reshaped, Y_reshaped, Q_reshaped, ds
        gc.collect()

    except Exception as e:
        logging.error(f"Error processing year {year}: {e}")
        
        
