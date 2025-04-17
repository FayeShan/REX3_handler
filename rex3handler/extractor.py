"""Unpack downloaded ZIPs."""
from __future__ import annotations

import os
import zipfile
from pathlib import Path

from tqdm import tqdm

__all__ = ["unzip_dir"]


def unzip_dir(zip_dir: str | os.PathLike = "downloads", extract_to: str | os.PathLike = "unzipped") -> None:
    """Unpack each `*.zip` into a *single* directory named after the archive.

    If the archive already contains a root folder identical to its own stem
    (e.g. *REX3_1999/…* inside **REX3_1999.zip**), we avoid creating the
    extra level so the final path is just  `<extract_to>/REX3_1999/…`.
    """
    
    zip_dir = Path(zip_dir)
    extract_to = Path(extract_to)
    extract_to.mkdir(parents=True, exist_ok=True)

    for zip_path in tqdm(list(zip_dir.glob("*.zip")), desc="Unzipping", unit="file"):
        try:
            with zipfile.ZipFile(zip_path, "r") as zf:
                # Collect the set of top‑level paths in the archive (excluding dirs)
                roots = {name.split("/", 1)[0] for name in zf.namelist() if name.strip("/")}
                single_root = len(roots) == 1 and next(iter(roots)) == zip_path.stem

                if single_root:
                    # Archive already has its own folder → extract directly to `extract_to`
                    zf.extractall(extract_to)
                else:
                    # No root folder → create one ourselves
                    target = extract_to / zip_path.stem
                    target.mkdir(exist_ok=True)
                    zf.extractall(target)
        except zipfile.BadZipFile:
            print(f" Skipping bad ZIP: {zip_path.name}")