"""
WuWa Mod Manager

1. Installing mods
    Will read downloads folder to find the most recent .zip file, which is assumed to be a mod.
    Then, this zip will be extracted to "SavedMods" folder.
    An optional mod name will be asked, which will be used to rename the entry of the mod in modlist.json

2. Deleting mods
    Will read modlist.json to find the provided mod name and delete the corresponding folder in "SavedMods"
    and "Mods" folders.

3. Toggling mods
    Presents the user with the installed-mods list and lets them
    flip the **enabled/disabled** state of any subset in one go.
    When a mod becomes **enabled** its files are copied from
    "SavedMods" to "Mods"; when it becomes **disabled** its folder
    is removed from "Mods".

Mod names also work as group/paths.
For example the name "carlotta<sep>black" means there's a mod named "black" in the "carlotta" group.
This is used to toggle any other mods active in the same group, so that only one mod of the group can be active at a time.
"""

"""
MODLIST Structure:

[
    {"name": "mod1", "path": ["SAVED_MODS_FOLDER/mod1"], "enabled": True},
    {"name": "carlotta-black", "path": ["SAVED_MODS_FOLDER/carlotta-black/carlotta_weapon", "SAVED_MODS_FOLDER/carlotta-black/character"], "enabled": True},
]

"""

from enum import Enum
import json
import os
from pathlib import Path
from typing import  List, Tuple, TypedDict
from typing import TypedDict, List


# ────────────────────────────
#  Paths & constants
# ────────────────────────────
DOWNLOADS_FOLDER = Path(r"C:\Users\Hyvnt\Downloads")
SAVED_MODS_FOLDER = Path(r"C:\Users\Hyvnt\AppData\Roaming\XXMI Launcher\WWMI\SavedMods")
ACTIVE_MODS_FOLDER = Path(r"C:\Users\Hyvnt\AppData\Roaming\XXMI Launcher\WWMI\Mods")
MODLIST_FILE = SAVED_MODS_FOLDER / "modlist.json"


# ────────────────────────────
#  Data shapes
# ────────────────────────────
class ModObject(TypedDict):
    name: str
    path: List[str]  # one or more folders (relative to SAVED_MODS_FOLDER)
    enabled: bool


type ModList = List[ModObject]


class FolderValidation(Enum):
    NOT_MOD = 0
    SINGLE_MOD = 1
    MULTI_MODS = 2


# ────────────────────────────
#  JSON helpers
# ────────────────────────────
def get_modlist() -> ModList:
    if not MODLIST_FILE.exists():
        return []
    try:
        with MODLIST_FILE.open(encoding="utf-8") as fh:
            raw: list[dict] = json.load(fh)
    except (json.JSONDecodeError, OSError):
        print("[ ! ] Corrupted modlist, resetting.")
        return []

    out: ModList = []
    for item in raw:
        if not isinstance(item, dict) or "name" not in item:
            continue
        out.append(
            ModObject(
                name=str(item["name"]),
                path=[str(p) for p in item.get("path", [])],
                enabled=bool(item.get("enabled", False)),
            )
        )
    return out


def save_modlist(modlist: ModList) -> None:
    with MODLIST_FILE.open("w", encoding="utf-8") as fh:
        json.dump(modlist, fh, indent=4, ensure_ascii=False)


# ────────────────────────────
#  Boot-strapping
# ────────────────────────────
def ensure_directories() -> None:
    for d in (SAVED_MODS_FOLDER, ACTIVE_MODS_FOLDER):
        os.makedirs(d, exist_ok=True)
    if not MODLIST_FILE.exists():
        MODLIST_FILE.write_text("[]", encoding="utf-8")

# - ────────────────────────────
#  Folder validation
# - ────────────────────────────
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
