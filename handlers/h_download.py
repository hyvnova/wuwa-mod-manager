"""
download_handler

Lets the user either

1. pick one / many of the 12 newest Wuthering Waves mods, or
2. run a text search and pick from those results,

then downloads every chosen mod into DOWNLOADS_FOLDER.

All I/O goes through IOProvider so the handler stays UI-agnostic.
"""

from pathlib import Path
from typing import List, Tuple, Union

from bananas import (
    API_MOD_TYPE,
    download_mod,
    get_recent_mods,
    search_mod,
)
from core import DOWNLOADS_FOLDER, TEMP_FOLDER
from get_input import get_menu_input
from io_provider import IOProvider


# ───────────────────────── helpers ──────────────────────────
def _pretty_mod_line(mod: API_MOD_TYPE) -> str:
    return f"{mod.name}  —  {mod.link}"


def _download_batch(mods: List[API_MOD_TYPE], output_fn) -> None:
    for m in mods:
        output_fn(f"[ / ] Downloading {m.name} …")
        try:
            path: Path = download_mod(m, dst=DOWNLOADS_FOLDER)
            output_fn(f"\t[ + ] Saved → {path.resolve()}")

            # Create banana id file, so it can be used later
            bananaid_path = TEMP_FOLDER / f"{m.name}.bananaid"
            with open(bananaid_path, "w", encoding="utf-8") as f:
                f.write(str(m.id))
            output_fn(f"\t[ + ] Banana ID saved → {bananaid_path.resolve()}")


        except Exception as exc:  # noqa: BLE001
            output_fn(f"\t[ ! ] Failed: {exc}")

    output_fn("\n[ + ] Download complete.")

# ──────────────────────── mod picker ───────────────────────
def _pick_mods(mods: List[API_MOD_TYPE], prompt: str) -> List[API_MOD_TYPE]:
    """
    Ask the user to choose mods from *mods* (can be many -> space separated).
    Returns the chosen list (can be empty).
    """
    sel: Union[int, Tuple[int, ...]] = get_menu_input(
        zero_option_text="[ 0 ] None",
        prompt=prompt,
        options=[_pretty_mod_line(m) for m in mods],
        space_separated=True,
    )
    sel = (sel,) if isinstance(sel, int) else sel
    return [mods[i - 1] for i in sel if 1 <= i <= len(mods)]


# ─────────────────────── public handler ─────────────────────
def download_handler() -> None:
    """
    Main entry:     show latest mods ➜ ask if they’d rather search ➜
                    pick indexes ➜ download each.
    """
    input_fn, output_fn = IOProvider().get_io()

    # 2 ─ ask whether to search instead
    output_fn("\n")
    choice = input_fn("Do you want to search? (y/N): ").strip().lower()

    if choice.startswith("y") or not choice:  # default to search if empty
        # 2-A ─ search flow
        output_fn("\n")
        query = input_fn("Search query: ").strip()
        if not query:
            output_fn("No query entered → aborting search.")
            return

        output_fn(f"\n\t [ / ] Searching for “{query}” (This can take a bit)...")

        results = search_mod(query, limit=12)
        if not results:
            output_fn("No mods match that query.")
            return

        output_fn(" Results ".center(40, "─"))
        for idx, m in enumerate(results, 1):
            output_fn(f"[ {idx:>2} ] {_pretty_mod_line(m)}")

        chosen = _pick_mods(results, prompt="Indexes to download (space-separated): ")
        if not chosen:
            output_fn("Nothing selected.")
            return
        _download_batch(chosen, output_fn)
        return
    
    else:
        # 1 ─ show the 12 newest mods
        recent: List[API_MOD_TYPE] = get_recent_mods(limit=12)
        output_fn(" Latest Mods on GameBanana ")

        # 2-B ─ recent-list flow
        chosen = _pick_mods(recent, prompt="Indexes to download (space-separated): ")
        if not chosen:
            output_fn("Nothing selected.")
            return

        _download_batch(chosen, output_fn)
