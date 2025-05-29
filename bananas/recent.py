from dataclasses import dataclass
import re
import requests
from typing import List, Dict


from bananas.shared import GAME_ID, URL, INDEX_EP, DATA_EP, FIELDS, API_MOD_TYPE, MAX_PER


# ───────────────────────── helpers ──────────────────────────

def _fetch_ids(limit: int) -> List[int]:
    ids: List[int] = []
    page, per_page = 1, min(limit, MAX_PER)

    while len(ids) < limit:
        params = {
            "_nPage": page,
            "_nPerpage": per_page,  # ← exact field-name
            "_aFilters[Generic_Game]": GAME_ID,
        }
        res = requests.get(INDEX_EP, params=params, timeout=10)
        res.raise_for_status()
        records = res.json()["_aRecords"]
        if not records:
            break
        ids.extend(rec["_idRow"] for rec in records)
        page += 1

    print(f"Fetched {len(ids)} mod IDs (limit={limit})")
    return ids[:limit]


def _fetch_details(mod_ids: List[int]) -> List[API_MOD_TYPE]:
    """
    Bulk-fetch the name, page link and a thumbnail for every mod-ID.
    Returns a list of dicts; skips any record missing one of the fields.
    """
    if not mod_ids:
        return []

    params = {
        "itemtype[]": ["Mod"] * len(mod_ids),
        "itemid[]": mod_ids,
        "fields[]": [FIELDS] * len(mod_ids),
        "return_keys": 1,
    }
    res = requests.get(DATA_EP, params=params, timeout=10)
    res.raise_for_status()

    mods_json = res.json()  # already a list of dicts
    out: List[API_MOD_TYPE] = []

    for mod in mods_json:
        name = mod.get("name")
        link = mod.get("Url().sProfileUrl()")
        thumb = mod.get("Preview().sStructuredDataFullsizeUrl()")

        if name and link and thumb:
            out.append(API_MOD_TYPE(name=name, link=link, thumb=thumb))

    return out


# ─────────────────────── public façade ──────────────────────
def get_recent_mods(limit: int = 10) -> List[API_MOD_TYPE]:
    if limit <= 0:
        return []
    mids = _fetch_ids(limit)
    return _fetch_details(mids)
