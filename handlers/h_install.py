from operator import is_
import os
import shutil
from time import sleep
from typing import  Dict, List
import zipfile
from pathlib import Path
from get_input import get_menu_input
from core import (
    DOWNLOADS_FOLDER,
    SAVED_MODS_FOLDER,
    ItemType,
    ModObject,
    get_modlist,
    is_valid_mod_folder,
    save_modlist,
)
from io_provider import IOProvider


# ────────────────────────────
#  Extraction helpers
# ────────────────────────────
def extract_zip(
    zip_path: Path, extract_to: Path | None = None
) -> Path:

    output_fn = IOProvider().get_output()

    target_dir = extract_to or zip_path.parent
    extracted_path = target_dir / zip_path.stem
    try:
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(extracted_path)
        return extracted_path
    except Exception as exc:
        output_fn(f"[ FATAL ] Failed to extract {zip_path.name}: {exc}")
        raise exc


def collapse_to_mod_folder(path: Path) -> Path:
    """Walk through single-child wrappers until we hit a dir with mod.ini."""
    current = path
    while current.is_dir():
        if (current / "mod.ini").is_file():
            return current
        subdirs = [p for p in current.iterdir() if p.is_dir()]
        if len(subdirs) != 1:  # zero OR many → let validator decide
            return current
        current = subdirs[0]
    return current  # sanity fallback


def promote_to_root(mod_root: Path, extracted_root: Path, root_folder: Path) -> Path:
    """
    Move the real mod folder (`mod_root`) directly under `root_folder`
    and nuke the temporary extraction tree.
    Returns the final on-disk path of the mod.
    """
    if mod_root.parent == root_folder:
        return mod_root  # already in the right place

    dest = root_folder / mod_root.name
    if dest.exists():
        shutil.rmtree(dest)
    shutil.move(str(mod_root), dest)

    # clean the now-empty wrapper(s)
    shutil.rmtree(extracted_root, ignore_errors=True)
    return dest


def validate_and_collect(into: Dict[str, List[Path]], zip_file: Path) -> None:
    output_fn = IOProvider().get_output()
    output_fn(f"\t[ / ] Checking {zip_file.name}")

    # 1. unzip
    extracted_root = extract_zip(zip_file, SAVED_MODS_FOLDER)

    # 2. find the actual mod dir
    mod_root = collapse_to_mod_folder(extracted_root)

    # 3. promote it (so v33 ends up in saved_mods, wrapper dies)
    mod_root = promote_to_root(mod_root, extracted_root, SAVED_MODS_FOLDER)

    # 4. validate
    status, name, paths = is_valid_mod_folder(mod_root)

    if status == False:
        output_fn(f"\t[ ! ] {zip_file.name} isn't a mod, discarding.")
        shutil.rmtree(mod_root, ignore_errors=True)
        return

    into.update({name: paths})


def install_handler() -> None:
    """
    Installs one or more .zip mods from the Downloads folder.
    """

    # Get input and output functions from IOProvider
    (input_fn, output_fn) = IOProvider().get_io()

    # Find all .zip files in the Downloads folder, sorted by modification time (newest first)
    zips = sorted(DOWNLOADS_FOLDER.glob("*.zip"), key=os.path.getmtime, reverse=True)

    if not zips:
        output_fn("No .zip files in Downloads.")
        return 

    # Prompt user to select which mods to install
    sel = get_menu_input(
        zero_option_text="[ 0 ] Any valid mod",
        prompt="Indexes to install (space-separated): ",
        options=[z.name for z in zips],
        space_separated=True,
    )

    # Normalize selection to a tuple
    sel = (sel,) if isinstance(sel, int) else sel

    # Will hold valid mods to install {name: [paths]}
    chosen: Dict[str, List[Path]] = {}

    # If user selected 0, validate and collect all zips; otherwise, only selected ones
    if 0 in sel:
        for z in zips:
            validate_and_collect(chosen, z)
    else:
        for idx in sel:
            if 1 <= idx <= len(zips):
                validate_and_collect(chosen, zips[idx - 1])

    output_fn(f"[ / ] {len(chosen)} valid mods found, installing…")
    modlist = get_modlist()

    # Add or update mods in the modlist
    for name, paths in chosen.items():

        # Check if the mod already exists in the modlist
        existing: ModObject = next((m for m in modlist if m.name == name and m.type == ItemType.MOD), None) # type: ignore
        str_paths = [str(p) for p in paths]

        if existing:
            if existing.path == str_paths:
                output_fn(f"\t[ = ] {name} already present.")
            else:
                output_fn(f"\t[ + ] Updating {name}")
                existing.path = str_paths
            continue

        # Add new mod entry
        modlist.append(ModObject(name=name, path=str_paths, enabled=False, date=0, gb_id=None))
        output_fn(f"\t[ + ] Added {name}")

    # Save the updated modlist
    save_modlist(modlist)
