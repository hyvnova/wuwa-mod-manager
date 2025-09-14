"""Download helpers for GameBanana mods."""

import re, os, time, random, requests
from pathlib import Path
from requests.exceptions import RequestException
from constants import DOWNLOADS_FOLDER
from bananas.shared import API_MOD_TYPE

# retry / timeout settings
HTTP_TIMEOUT = 15  # seconds
MAX_RETRIES = 4
BACKOFF_BASE = 0.8  # sec
CHUNK = 16 * 1024  # 16 KiB stream-chunk


# -------------------------------------------------------------
#  low-level helpers
# -------------------------------------------------------------
def _safe_get(url: str, **kwargs) -> requests.Response:  # type: ignore
    """GET with retries + exponential back-off."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return requests.get(url, timeout=HTTP_TIMEOUT, **kwargs)
        except RequestException as exc:
            if attempt == MAX_RETRIES:
                raise
            sleep = BACKOFF_BASE * (2 ** (attempt - 1)) + random.uniform(0, 0.4)
            time.sleep(sleep)


GB_CORE_DATA = "https://api.gamebanana.com/Core/Item/Data"


def _latest_file_record(mod_id: int) -> dict:
    """Return the dict for the newest file attached to a mod id."""
    params = {
        "itemtype": "Mod",
        "itemid": mod_id,
        "fields": "Files().aFiles()",
        "return_keys": 1,
    }
    data = _safe_get(GB_CORE_DATA, params=params).json()
    data = data[0] if isinstance(data, list) else data

    files_dict = data.get("Files().aFiles()", {})
    if not files_dict:
        raise RuntimeError("No downloadable files for this mod")

    # newest by timestamp
    return max(files_dict.values(), key=lambda f: f["_tsDateAdded"])


# file info now *uses that record directly* — no second API call
def _file_info_from_record(rec: dict) -> dict:
    return {
        "name": rec["_sFile"],  # original filename
        "url": rec["_sDownloadUrl"],
    }

def download_mod(mod: API_MOD_TYPE, dst: Path = DOWNLOADS_FOLDER) -> Path:
    """Download the newest file for a mod into dst and return its path."""
    m = re.search(r"/mods/(\d+)", mod.link)
    if not m:
        raise ValueError(f"Cannot parse mod-ID from {mod.link}")
    mod_id = int(m.group(1))

    file_rec = _latest_file_record(mod_id)
    info     = _file_info_from_record(file_rec)

    # sanitise filename
    safe_name = re.sub(r"[^\w.\- ]+", "_", info["name"]).strip() or "mod_download"
    
    if not Path(safe_name).suffix:  # add ext if missing
        ext = info["url"].split("?")[0].rsplit(".", 1)[-1]
        safe_name += f".{ext}"

    dest = dst / safe_name
    print(f"[ / ] Downloading {mod.name}  →  {dest.name}")

    with _safe_get(info["url"], stream=True) as r, open(dest, "wb") as f:
        r.raise_for_status()
        for chunk in r.iter_content(CHUNK):
            f.write(chunk)

    return dest
