from pathlib import Path
from typing import Dict, List

from bananas import search
from bananas.download import download_mod
from bananas.shared import API_MOD_TYPE
from bisextypes import ModObject, TypeOfItem
from core import get_modlist, save_modlist
from io_provider import IOProvider

# Reuse install helpers for extraction/validation
from .h_install import validate_and_collect
from constants import DOWNLOADS_FOLDER


def update_handler() -> None:
    """Update installed mods by fetching their latest archives from GameBanana.

    Strategy (interactive, robust baseline):
    - For each ModObject:
      - If gb_id is missing, search by name (top 3 results) and ask user to choose.
      - If gb_id is present, attempt a name-based search to obtain a concrete
        API_MOD_TYPE (best effort), otherwise skip with a warning.
      - Download newest file, validate and collect extracted paths, then upsert
        the mod entry in the modlist.

    Groups are processed by updating each member individually.
    """
    input_fn, output_fn = IOProvider().get_io()

    modlist = get_modlist()
    if not modlist:
        output_fn("No mods to update.")
        return

    output_fn("[ / ] Checking for updates…")

    def _choose_by_search(name: str) -> API_MOD_TYPE | None:
        results = search.search_mod(name, limit=3)
        if not results:
            output_fn(f"\t[ ! ] No results found for '{name}'.")
            return None
        output_fn(f"\t[ / ] Found {len(results)} potential matches:")
        for i, result in enumerate(results, 1):
            output_fn(f"\t[ {i} ] {result.name} (ID: {result.id})")
        try:
            choice = int(input_fn(f"\t[ ? ] Pick 1-{len(results)} (0 to skip): "))
        except ValueError:
            return None
        if choice == 0 or not (1 <= choice <= len(results)):
            return None
        return results[choice - 1]

    def _update_mod(mod: ModObject) -> None:
        output_fn(f"\t[ / ] Updating '{mod.name}' …")

        chosen: API_MOD_TYPE | None = _choose_by_search(mod.name)
        if chosen is None:
            output_fn(f"\t[ ! ] Skipping '{mod.name}'.")
            return

        # Remember gb_id if user approved a choice
        try:
            mod.gb_id = int(chosen.id)  # type: ignore[arg-type]
        except Exception:
            pass

        # Download and validate
        try:
            zip_path: Path = download_mod(chosen, dst=DOWNLOADS_FOLDER)
        except Exception as exc:
            output_fn(f"\t[ ! ] Download failed: {exc}")
            return

        details: Dict[str, List[Path]] = {}
        try:
            validate_and_collect(details, zip_path)
        except Exception as exc:
            output_fn(f"\t[ ! ] Validation failed: {exc}")
            return

        ml = get_modlist()
        for name, paths in details.items():
            existing: ModObject | None = next(
                (m for m in ml if m.type == TypeOfItem.MOD and m.name == name),
                None,
            )
            str_paths = [str(p) for p in paths]
            if existing:
                if existing.path != str_paths:
                    output_fn(f"\t[ + ] Updated paths for {name}")
                    existing.path = str_paths
                else:
                    output_fn(f"\t[ = ] {name} already up to date.")
            else:
                ml.append(ModObject(name=name, path=str_paths, enabled=False, date=0, gb_id=mod.gb_id))
                output_fn(f"\t[ + ] Added {name}")
        save_modlist(ml)

    # Sequential for determinism; easy to parallelize later.
    for item in modlist:
        if item.type == TypeOfItem.GROUP:
            output_fn(f"\t[ / ] Updating group: {item.name}")
            for member in item.members:  # type: ignore[attr-defined]
                _update_mod(member)
        elif item.type == TypeOfItem.MOD:
            _update_mod(item)  # type: ignore[arg-type]

    output_fn("[ + ] Update complete.")
