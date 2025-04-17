__all__ = [
    "download_files",
    "unzip_dir",
    "convert_years_to_zarr",
]

from importlib.metadata import version
__version__ = version(__package__)

from .downloader import download_files  # re‑export for convenience
from .extractor import unzip_dir        # re‑export
from .converter import convert_years_to_zarr  # re‑export