import shutil
from typing import Dict, List, Tuple
import zipfile

from pathlib import Path
from get_input import get_menu_input
from core import DOWNLOADS_FOLDER, SAVED_MODS_FOLDER, ModObject, get_modlist, save_modlist, FolderValidation


# ────────────────────────────
#  Extraction helpers
# ────────────────────────────
def extract_zip(zip_path: Path, extract_to: Path | None = None) -> bool:
    target_dir = extract_to or zip_path.parent
    try:
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(target_dir)
        return True
    except Exception as exc:
        print(f"[ FATAL ] Failed to extract {zip_path.name}: {exc}")
        return False


# ────────────────────────────
#  Validation
# ────────────────────────────



def is_valid_mod_folder(folder: Path) -> Tuple[FolderValidation, str, List[Path]]:
    """
    Returns a tuple of:
    0. FolderValidation
    1. Name of the mod (name of root folder)
    2. List of paths that contain .ini files (if SINGLE_MOD or MULTI_MODS)

    Rule:
    - If the current folder contains one or more .ini files, it's SINGLE_MOD (collect all descendant subpaths with .ini).
    - If not, but it contains several subfolders, and those subfolders contain .ini files, it's MULTI_MODS.
    - If there are no .ini files anywhere relevant, it's NOT_MOD.
    """
    if not folder.is_dir():
        return (FolderValidation.NOT_MOD, "", [])

    root = folder
    while True:
        # Case 1. The root contains a .ini file
        # If so this is a single mod
        if any(f.is_file() and f.suffix == ".ini" for f in root.iterdir()):
            return (FolderValidation.SINGLE_MOD, root.name, [root])

        # Case 2. There is only 1 subfolder.
        subdirs = [d for d in root.iterdir() if d.is_dir()]

        # Move to the next subfolder if there is only one
        if len(subdirs) == 1:
            root = subdirs[0]
            continue

        # Case 3. There are multiple subfolders
        # If some of the subfolders contain .ini files, this is a multi-mods folder
        paths: List[Path] = []
        if len(subdirs) > 1:
            for sub in subdirs:
                if any(f.is_file() and f.suffix == ".ini" for f in sub.iterdir()):
                    paths.append(sub)

            # If no valid subfolders were found, this is not a mod folder
            if not paths:
                return (FolderValidation.NOT_MOD, "", [])

            # If there is only one valid subfolder, this is a single mod folder
            if len(paths) == 1:
                return (FolderValidation.SINGLE_MOD, paths[0].name, paths)

            # If there are multiple valid subfolders, this is a multi-mods folder
            return (FolderValidation.MULTI_MODS, "", paths)


def validate_and_collect(into: Dict[str, List[Path]], zip_file: Path) -> None:
    """Extract zip → validate → populate `into` dict (mod_name -> [paths])"""
    print(f"\t[ / ] Checking {zip_file.name}")

    if not extract_zip(zip_file, SAVED_MODS_FOLDER):
        return

    root = SAVED_MODS_FOLDER / zip_file.stem
    status, name, paths = is_valid_mod_folder(root)

    if status is FolderValidation.NOT_MOD:
        print(f"\t[ ! ] {zip_file.name} isn't a mod, discarding.")
        shutil.rmtree(root, ignore_errors=True)
        return

    into.update({name: paths})


def install_handler() -> None:
    """
    Installs one or more .zip mods from the Downloads folder.
    """

    zips = sorted(DOWNLOADS_FOLDER.glob("*.zip"), key=os.path.getmtime, reverse=True)
    
    if not zips:
        print("No .zip files in Downloads.")
        return go_back()

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

    print(f"[ / ] {len(chosen)} valid mods found, installing…")
    modlist = get_modlist()

    for name, paths in chosen.items():
        existing = next((m for m in modlist if m["name"] == name), None)
        str_paths = [str(p) for p in paths]

        if existing:
            if existing["path"] == str_paths:
                print(f"\t[ = ] {name} already present.")
            else:
                print(f"\t[ ~ ] Updating {name}")
                existing["path"] = str_paths
            continue

        modlist.append(ModObject(name=name, path=str_paths, enabled=False))
        print(f"\t[ + ] Added {name}")

    save_modlist(modlist)
    go_back()
