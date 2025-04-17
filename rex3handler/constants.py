"""Dataset metadata shared across sub‑modules."""
# link of REX3
ZENODO_RECORD_ID: str = "10354283"
BASE_URL: str = f"https://zenodo.org/records/{ZENODO_RECORD_ID}/files"

ALL_FILES: set[str] = {
    "matlab code to calculate MRIO results (Figure 2-5).zip",
    "matlab code to compile REX3.zip",
    "R code for regionalized BD impact assessment based on LUH2 data and maps (Figure 1).zip",
    "R code to illustrate sankeys – Figure 3–5, S10.zip",
    "REX3_Labels.zip",
}

ALL_FILES.update({f"REX3_{year}.zip" for year in range(1995, 2023)})