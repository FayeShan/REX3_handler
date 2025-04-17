# REX3Handler

**REX3Handler** is a Python toolkit to **download, extract, and convert** the highly resolved **REX3 MRIO database** into chunked, analysis-ready **Zarr** format. It enables seamless access and integration into Python workflows — no MATLAB required.

---

## 🌍 About the REX3 Database

**REX3** (Resolved EXIOBASE version 3) is a high-resolution Multi-Regional Input-Output (MRIO) database developed by [Livia Cabernard](https://scholar.google.com/citations?hl=en&user=5EtKtjoAAAAJ) as part of the study:

> “Biodiversity impacts of recent land-use change driven by increases in agri-food imports”  
> Published in *Nature Sustainability* — [Read the article](https://www.nature.com/articles/s41893-023-01169-6)


### 🧬 What's inside REX3?

- **189 countries**, **163 sectors**
- **Time series from 1995 to 2022**
- Includes **climate impacts**, **PM health**, **water stress**, **biodiversity impacts** (land occupation, land-use change, eutrophication)
- Based on:
  - **EXIOBASE 3.8**
  - **Eora26**
  - **FAOSTAT production data**
  - **BACI trade data**
  - **LUH2 land use harmonization**
- Compliant with **UNEP-SETAC environmental assessment guidelines**

### 📦 File contents (per year)

Each `REX3_YYYY.zip` file contains:

- `T_REX3.mat`: Transaction matrix  
- `Y_REX3.mat`: Final demand matrix  
- `Q_REX3.mat`, `Q_Y_REX3.mat`: Satellite extensions (economic & final demand)

Labels for all matrices, countries, sectors, and extensions are provided in a separate `REX3_Labels.zip`.

---

## 💡 Why use REX3Handler?

The REX3 dataset is primarily provided in MATLAB `.mat` format, which may not be ideal for many researchers, particularly in the Earth system, environmental economics, or data science communities who work primarily in **Python**.

**REX3Handler** was built to:

- ✅ Automate downloading from [Zenodo](https://zenodo.org/records/10354283)
- ✅ Unpack ZIP archives
- ✅ Convert `.mat` files into Python-native `xarray.Dataset` objects in `.zarr` format
- ✅ Enable fast, scalable, multi-year MRIO analysis
- ✅ Provide a foundation for future development: MRIO analytics, visualization, decomposition, and more (coming soon)

---

## 🎾 Quick‑start

```bash
# Install 
pip install rex3handler
```

## 💻 Download options
### 1 Download the **entire archive** (all years + misc.) using 8 threads
```bash
rex3 download all --workers 8
```

### 2  Download a **single year** (1999) using 4 threads (~4GB per year)
```bash
rex3 download single --year 1999 --workers 4
```

### 3  Download a **range of years** (e.g., 2018–2023) using 8 threads
```bash
rex3 download range --start 2018 --end 2023 --workers 8
```

## 📲 Extract and convert
### Unzip all downloaded archives
```bash
rex3 extract
```

### Convert all extracted .mat files into chunked Zarr format (~2GB per year)
```bash
rex3 convert
```


### 🍏 Using from Python directly

If you prefer working inside Jupyter notebooks or Python scripts, you can also import the core functionality directly:

```python
from rex3handler import download_files, unzip_dir, convert_years_to_zarr

# Download a single year
download_files(mode="single", year=1999)

# Extract
unzip_dir()

# Convert
convert_years_to_zarr(years=[1999])
```


## ⛱️ Load and explore in Python

```python
import xarray as xr

# Open one year's data
ds = xr.open_zarr("REX3ZARR/1999.zarr", consolidated=True)

# Access the transaction matrix
T_array = ds["T"]

# Convert to NumPy array if needed
T_numpy = T_array.values

# Check dimensions and shape
print(T_array.dims)
print(T_array.shape)
```