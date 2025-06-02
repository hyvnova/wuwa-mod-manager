import re
import requests
from datetime import datetime, timezone
from typing import List, Dict

from bananas.shared import API_MOD_TYPE  # now has .date attribute

# ────────────────────────── endpoints & constants ──────────────────────────
URL = "https://gamebanana.com/games/20357"  # overwrite at runtime if needed
INDEX_EP = "https://gamebanana.com/apiv10/Mod/Index"
DATA_EP = "https://api.gamebanana.com/Core/Item/Data"
FIELDS = (
    "name,"
    "Url().sProfileUrl(),"
    "Preview().sStructuredDataFullsizeUrl(),"
    "Files().aFiles()"  # new - gives timestamps
)
MAX_PERPAGE = 50
TIMEOUT = 10
ID_BATCH_SIZE = 20  # Nuevo límite seguro de IDs por batch


# ────────────────────────── internal helpers ──────────────────────────
def _game_id() -> int:
    m = re.search(r"/(?:games|mods/games)/(\d+)", URL)
    if not m:
        raise ValueError(f"Cannot parse game id from {URL}")
    return int(m.group(1))


def _safe_get(url: str, **kw) -> requests.Response:  # type: ignore
    return requests.get(url, timeout=TIMEOUT, **kw)


def _page_ids(gid: int, page: int, per: int) -> List[int]:
    params = {
        "_nPage": page,
        "_nPerpage": per,
        "_aFilters[Generic_Game]": gid,
    }
    r = _safe_get(INDEX_EP, params=params)
    r.raise_for_status()
    return [rec["_idRow"] for rec in r.json()["_aRecords"]]


def _parse_mod(raw: dict, mod_id: int | None = None) -> API_MOD_TYPE:
    """
    raw  API_MOD_TYPE, extracting newest file's _tsDateAdded.
    id_row se usará si no hay "_idRow" dentro de raw.
    """
    files_blob: Dict[str, dict] = raw.get("Files().aFiles()", {})
    newest_ts: int | None = None
    if files_blob:
        newest_ts = max(f["_tsDateAdded"] for f in files_blob.values())

    mod_id = raw.get("_idRow", mod_id)  # flexible por si el id viene externo

    return API_MOD_TYPE(
        name=raw["name"],
        link=raw["Url().sProfileUrl()"],
        thumb=raw["Preview().sStructuredDataFullsizeUrl()"],
        date=(newest_ts or 0),
        id=mod_id,
    )


def _fetch_batch(ids: List[int]) -> List[API_MOD_TYPE]:
    # Dividir en lotes más pequeños para evitar error de URI demasiado larga
    results = []
    for i in range(0, len(ids), ID_BATCH_SIZE):
        batch = ids[i:i+ID_BATCH_SIZE]
        params = {
            "itemtype[]": ["Mod"] * len(batch),
            "itemid[]": batch,
            "fields[]": [FIELDS] * len(batch),
            "return_keys": 1,
        }
        r = _safe_get(DATA_EP, params=params)
        r.raise_for_status()
        mods_raw = r.json()  # esto puede ser dict, no list!


        # print("[DEBUG] mods_raw recibido:")
        # print(repr(mods_raw))

        # Si es dict, los keys son los IDs
        if isinstance(mods_raw, dict):
            for key, val in mods_raw.items():
                try:
                    mod_id = int(key)
                except Exception:
                    mod_id = key
                results.append(_parse_mod(val, mod_id=mod_id))
        # Si es list, intentar como antes
        elif isinstance(mods_raw, list):
            results.extend([_parse_mod(m) for m in mods_raw])
        else:
            print("[WARN] mods_raw tiene formato inesperado:", type(mods_raw))
    return results


# ────────────────────────── public API ──────────────────────────

def get_recent_mods(limit: int = 10) -> List[API_MOD_TYPE]:
    if limit <= 0:
        return []

    gid, page, collected = _game_id(), 1, []
    while len(collected) < limit:
        ids = _page_ids(gid, page, MAX_PERPAGE)
        if not ids:
            break
        collected.extend(_fetch_batch(ids))
        page += 1
    return collected[:limit]


def search_mod(query: str, limit: int = 10) -> List[API_MOD_TYPE]:
    query = query.strip().lower()
    if not query or limit <= 0:
        return []

    gid, page, hits = _game_id(), 1, []
    while len(hits) < limit:
        ids = _page_ids(gid, page, MAX_PERPAGE)
        if not ids:
            break
        for mod in _fetch_batch(ids):
            if query in mod.name.lower():
                hits.append(mod)
                if len(hits) == limit:
                    break
        page += 1
    return hits