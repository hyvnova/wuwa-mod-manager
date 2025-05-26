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

import json
import os
import sys
from pathlib import Path
from typing import Callable, Dict, List, TypedDict


# ────────────────────────────
#  Paths & constants
# ────────────────────────────
from typing import TypedDict, List
from path import Path
from zmq import Enum

from str_sort import sort_by_similitude


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



