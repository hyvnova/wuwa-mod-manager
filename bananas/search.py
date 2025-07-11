import re, time, random, requests
from typing import List, Dict
from requests.exceptions import RequestException
from bananas.shared import GAME_ID, URL, INDEX_EP, DATA_EP, FIELDS, API_MOD_TYPE, MAX_PER

CHUNK_SIZE = 10  # how many IDs per Data query
TIMEOUT = 10  # seconds per request
MAX_RETRIES = 7  # total attempts before giving up
BACKOFF_BASE = 1  # exponential base (sec)


def _safe_get(url: str, **kwargs) -> requests.Response: # type: ignore
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return requests.get(url, timeout=TIMEOUT, **kwargs)
        except RequestException as exc:
            if attempt == MAX_RETRIES:
                raise
            sleep_for = BACKOFF_BASE * (2 ** (attempt - 1))
            # jitter to avoid thundering herd
            time.sleep(sleep_for + random.uniform(0, 0.3))



def _page_ids(page: int, per: int) -> List[int]:
    params = {
        "_nPage": page,
        "_nPerpage": per,
        "_aFilters[Generic_Game]": GAME_ID,
    }
    r = _safe_get(INDEX_EP, params=params)
    r.raise_for_status()
    return [rec["_idRow"] for rec in r.json()["_aRecords"]]


def _fetch_details(ids: List[int]) -> List[API_MOD_TYPE]:
    out: List[API_MOD_TYPE] = []

    for i in range(0, len(ids), CHUNK_SIZE):
        chunk = ids[i : i + CHUNK_SIZE]
        params = {
            "itemtype[]": ["Mod"] * len(chunk),
            "itemid[]": chunk,
            "fields[]": [FIELDS] * len(chunk),
            "return_keys": 1,
        }
        r = _safe_get(DATA_EP, params=params)

        try:
            r.raise_for_status()
        except requests.exceptions.HTTPError as exc:
            if exc.response.status_code == 429:
                for attempt in range(1, MAX_RETRIES + 1):
                    # Calculate backoff time with exponential growth and jitter
                    backoff_time = BACKOFF_BASE * (2 ** (attempt - 1))
                    jitter = random.uniform(0, backoff_time * 0.2)  # 20% jitter
                    total_wait = backoff_time + jitter
                    
                    print(f"Rate limit hit. Attempt {attempt}/{MAX_RETRIES}, waiting {total_wait:.1f}s")
                    time.sleep(total_wait)
                    
                    r = _safe_get(DATA_EP, params=params)
                    try:
                        r.raise_for_status()
                        break  # Only break if the retry was successful
                    except requests.exceptions.HTTPError as exc:
                        if attempt == MAX_RETRIES:
                            raise exc  # Re-raise last exception if all retries failed
                        continue  # Continue to next retry attempt

        for mod in r.json():  # already list[dict]
            name = mod.get("name")
            link = mod.get("Url().sProfileUrl()")
            thumb = mod.get("Preview().sStructuredDataFullsizeUrl()")
            date = mod.get("_tsDateAdded", 0)  # default to 0 if not present
            id = mod.get("_idRow")
            if name and link and thumb and id:
                out.append(API_MOD_TYPE(name=name, link=link, thumb=thumb, id=id, date=date))

    return out


def search_mod(query: str, limit: int = 10) -> List[API_MOD_TYPE]:
    query = query.strip().lower()
    if not query or limit <= 0:
        return []

    page = 1
    matches: List[API_MOD_TYPE] = []

    while len(matches) < limit:
        ids = _page_ids(page, MAX_PER)
        if not ids:
            break  # done
        for batch in _fetch_details(ids):
            if query in batch.name.lower():
                matches.append(batch)
                if len(matches) == limit:
                    return matches
        page += 1

    return matches
