import os
import shutil
from typing import  Dict, List
import zipfile
from pathlib import Path
from get_input import get_menu_input
from core import (
    DOWNLOADS_FOLDER,
    SAVED_MODS_FOLDER,
    ModObject,
    get_modlist,
    is_valid_mod_folder,
    save_modlist,
    FolderValidation,
)
from io_provider import IOProvider


# ────────────────────────────
#  Extraction helpers
# ────────────────────────────
def extract_zip(
    zip_path: Path, extract_to: Path | None = None
) -> bool:

    output_fn = IOProvider().get_output()

    target_dir = extract_to or zip_path.parent
    try:
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(target_dir)
        return True
    except Exception as exc:
        output_fn(f"[ FATAL ] Failed to extract {zip_path.name}: {exc}")
        return False




def validate_and_collect(
        into: Dict[str, List[Path]], zip_file: Path) -> None:
    """Extract zip → validate → populate `into` dict (mod_name -> [paths])"""

    output_fn = IOProvider().get_output()

    output_fn(f"\t[ / ] Checking {zip_file.name}")

    if not extract_zip(zip_file, SAVED_MODS_FOLDER):
        return

    root = SAVED_MODS_FOLDER / zip_file.stem
    status, name, paths = is_valid_mod_folder(root)

    if status is FolderValidation.NOT_MOD:
        output_fn(f"\t[ ! ] {zip_file.name} isn't a mod, discarding.")
        shutil.rmtree(root, ignore_errors=True)
        return

    into.update({name: paths})


def install_handler() -> None:
    """
    Installs one or more .zip mods from the Downloads folder.
    """

    (input_fn, output_fn) = IOProvider().get_io()

    zips = sorted(DOWNLOADS_FOLDER.glob("*.zip"), key=os.path.getmtime, reverse=True)

    if not zips:
        output_fn("No .zip files in Downloads.")
        return 

    sel = get_menu_input(
        zero_option_text="[ 0 ] Any valid mod",
        prompt="Indexes to install (space-separated): ",
        options=[z.name for z in zips],
        space_separated=True,
    )

    # normalise to tuple
    sel = (sel,) if isinstance(sel, int) else sel
    chosen: Dict[str, List[Path]] = {}

    if 0 in sel:
        for z in zips:
            validate_and_collect(chosen, z)
    else:
        for idx in sel:
            if 1 <= idx <= len(zips):
                validate_and_collect(chosen, zips[idx - 1])

    output_fn(f"[ / ] {len(chosen)} valid mods found, installing…")
    modlist = get_modlist()

    for name, paths in chosen.items():
        existing = next((m for m in modlist if m["name"] == name), None)
        str_paths = [str(p) for p in paths]

        if existing:
            if existing["path"] == str_paths:
                output_fn(f"\t[ = ] {name} already present.")
            else:
                output_fn(f"\t[ ~ ] Updating {name}")
                existing["path"] = str_paths
            continue

        modlist.append(ModObject(name=name, path=str_paths, enabled=False))
        output_fn(f"\t[ + ] Added {name}")

    save_modlist(modlist)
    
