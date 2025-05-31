import re
import requests
from datetime import datetime, timezone
from typing import List, Dict

from bananas.shared import API_MOD_TYPE  # now has .date attribute

# ─────────────── endpoints & constants ────────────────
URL = "https://gamebanana.com/games/20357"  # overwrite at runtime if needed
INDEX_EP = "https://gamebanana.com/apiv10/Mod/Index"
DATA_EP = "https://api.gamebanana.com/Core/Item/Data"
FIELDS = (
    "name,"
    "Url().sProfileUrl(),"
    "Preview().sStructuredDataFullsizeUrl(),"
    "Files().aFiles()"  # new – gives timestamps
)
MAX_PERPAGE = 50
TIMEOUT = 10


# ─────────────── internal helpers ────────────────
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


def _parse_mod(raw: dict) -> API_MOD_TYPE:
    """
    raw → API_MOD_TYPE, extracting newest file’s _tsDateAdded.
    """
    files_blob: Dict[str, dict] = raw.get("Files().aFiles()", {})
    newest_ts = None
    if files_blob:
        newest_ts = max(f["_tsDateAdded"] for f in files_blob.values())

    # store as aware-UTC datetime; change to int if you prefer
    date_val = datetime.fromtimestamp(newest_ts, tz=timezone.utc) if newest_ts else None

    return API_MOD_TYPE(
        name=raw["name"],
        link=raw["Url().sProfileUrl()"],
        thumb=raw["Preview().sStructuredDataFullsizeUrl()"],
        date=date_val,
    )


def _fetch_batch(ids: List[int]) -> List[API_MOD_TYPE]:
    if not ids:
        return []

    params = {
        "itemtype[]": ["Mod"] * len(ids),
        "itemid[]": ids,
        "fields[]": [FIELDS] * len(ids),
        "return_keys": 1,
    }
    r = _safe_get(DATA_EP, params=params)
    r.raise_for_status()

    mods_raw = r.json()  # list[dict]
    return [_parse_mod(m) for m in mods_raw]


# ─────────────── public API ────────────────
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
