from pathlib import Path
import shutil
import time
from typing import Iterable, Generator

from core import (
    ACTIVE_MODS_FOLDER,
    SAVED_MODS_FOLDER,
    ModList,
    ModObject,
    FolderValidation,
    get_modlist,
    is_valid_mod_folder,
    save_modlist,
)
from io_provider import IOProvider

# ────────────────────────────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────────────────────────────


def _log_copy(src: Path, dest: Path, output) -> None:
    """Copy a folder while logging start/finish so hangs are obvious."""
    output(f"\t[ → ] Copying {src.name} to SavedMods…")
    t0 = time.perf_counter()
    shutil.copytree(src, dest)
    output(f"\t[ ✓ ] Copied in {time.perf_counter() - t0:,.1f}s.")


# ────────────────────────────────────────────────────────────────────────────────
# Core restore logic
# ────────────────────────────────────────────────────────────────────────────────


def restore_entry_from_paths(
    modlist: ModList,
    paths: Iterable[Path],
    *,
    delete_invalid: bool = False,
    save_to_savedmods: bool,
) -> None:
    """
    Scan *paths* for valid mods and make sure they’re present in *modlist*.

    The “no-duplicate-folder” rule:
        If a folder is already referenced by **any** multi-mod,
        another mod cannot claim that same folder.
    """

    output = IOProvider().get_output()

    # Build live view of multi-mod folders; keep it updated as we mutate
    multipath_paths: set[str] = {
        p for m in modlist if len(m["path"]) > 1 for p in m["path"]
    }

    for entry in paths:
        # ─── Reject stray files ─────────────────────────────────────────────
        if not entry.is_dir():
            if entry.is_file() and entry.name == "modlist.json":
                continue
            output(f"\t[ ! ] {entry.name} is not a directory.")
            if delete_invalid:
                shutil.rmtree(entry, ignore_errors=True)
                output(f"\t[ + ] Deleted {entry.name}.")
            continue

        # ─── Classify candidate folder ─────────────────────────────────────
        status, mod_name, mod_paths = is_valid_mod_folder(entry)

        if status == FolderValidation.NOT_MOD:
            output(f"\t[ ! ] {entry.name} is not a valid mod.")
            if delete_invalid:
                shutil.rmtree(entry, ignore_errors=True)
                output(f"\t[ + ] Deleted {entry.name}.")
            continue

        # ─── Ensure entry exists / update paths ────────────────────────────
        existing = next((m for m in modlist if m["name"] == mod_name), None)
        if not existing:
            existing = ModObject(name=mod_name, path=[], enabled=False)
            modlist.append(existing)
            output(f"\t[ + ] Added {mod_name}.")

        # For every discovered sub-path, apply duplicate-folder rule then add
        for p in mod_paths:
            p_str = str(p)
            if p_str in multipath_paths and len(existing["path"]) == 0:
                # Skip entire single-folder mod that clashes with a multi-mod
                output(
                    f"\t[ - ] Skipping {mod_name}: folder already "
                    "belongs to another multi-path mod."
                )
                break

            if p_str not in existing["path"]:
                existing["path"].append(p_str)
                if len(existing["path"]) > 1:
                    multipath_paths.add(p_str)  # now part of a multi-mod

        # ─── Copy to SavedMods if requested and not present ────────────────
        if save_to_savedmods and not (SAVED_MODS_FOLDER / mod_name).exists():
            _log_copy(entry, SAVED_MODS_FOLDER / mod_name, output)

    output(f"\t[ + ] {len(modlist)} mods tracked so far.")


# ────────────────────────────────────────────────────────────────────────────────
# Public entry point
# ────────────────────────────────────────────────────────────────────────────────


def rebuild_handler(*, delete_invalid: bool = True) -> None:
    """
    Re-create *modlist.json* from folders on disk, removing redundant entries.
    """

    output = IOProvider().get_output()
    output("- Rebuild modlist -".center(40, "="))
    output("This will ensure every valid mod in SavedMods or Mods is tracked.\n\n")

    modlist = get_modlist()

    # 1. Scan SavedMods  (no need to copy; they’re already there)
    restore_entry_from_paths(
        modlist,
        SAVED_MODS_FOLDER.iterdir(),
        delete_invalid=delete_invalid,
        save_to_savedmods=False,
    )

    # 2. Scan active Mods  (copy any missing ones to SavedMods)
    restore_entry_from_paths(
        modlist,
        ACTIVE_MODS_FOLDER.iterdir(),
        delete_invalid=delete_invalid,
        save_to_savedmods=True,
    )

    # 3. Purge single-mods whose folder is covered by a multi-mod
    multipath_set = {p for m in modlist if len(m["path"]) > 1 for p in m["path"]}
    to_drop = {
        m["name"]
        for m in modlist
        if len(m["path"]) == 1 and m["path"][0] in multipath_set
    }

    for n in to_drop:
        output(f"\t[ - ] Removing {n} (folder already in a multi-mod).")
    modlist[:] = [m for m in modlist if m["name"] not in to_drop]

    save_modlist(modlist)
    output("[ ✓ ] Rebuild complete.")
