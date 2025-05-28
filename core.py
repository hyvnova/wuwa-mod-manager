import os
from pathlib import Path
from get_input import get_confirmation
from io_provider import IOProvider

# ────────────────────────────
#  Paths & constants
# ────────────────────────────
USER_HOME = Path.home()
DOWNLOADS_FOLDER = USER_HOME / "Downloads"
APPDATA_FOLDER = Path(os.getenv("APPDATA", USER_HOME / "AppData" / "Roaming"))

WWMI_FOLDER = APPDATA_FOLDER / "XXMI Launcher" / "WWMI" # XXMI Mod Installer folder 

SAVED_MODS_FOLDER = WWMI_FOLDER / "SavedMods" # Folder where mods are saved after installation
ACTIVE_MODS_FOLDER = WWMI_FOLDER / "Mods" # Folder where active mods are copied to be used by the game
MODLIST_FILE = WWMI_FOLDER / "modlist.json" # File where the list of installed mods and groups are stored

ALLOWED_MODS_FILE = WWMI_FOLDER / "allowed_mods.json" # Allowed folder names. Since some mods don't contain a mod.ini and intead have something like "modname.ini"
# This file will keep track of the allowed folder names, so that the user can install mods without a mod.ini file.
# ────────────────────────────

# Debug Paths
# print(f"{USER_HOME}")
# print(f"{DOWNLOADS_FOLDER=}")
# print(f"{APPDATA_FOLDER=}")
# print(f"{SAVED_MODS_FOLDER=}")
# print(f"{ACTIVE_MODS_FOLDER=}")
# print(f"{MODLIST_FILE=}")

# If not downloads ask user to set up where stupid path where they their stupid mods
if not DOWNLOADS_FOLDER.exists():
    print(
        "[ ! ] The Downloads folder does not exist.\n"
        "Please set up your Downloads folder in your system settings.\n",
        "And fuck you.\n"
    )

    DOWNLOADS_FOLDER = Path(input("Enter ABSOLUTE PATH to your Downloads folder or the Folder where you install mods: "))
    # Assume path it's good. Profit $

# If appdata doesn't exist tell user to fucking find it
if not APPDATA_FOLDER.exists():
    print(
        "[ ! ] The AppData folder does not exist.\n"
        "Please set up your AppData folder in your system settings.\n",
        "And fuck you.\n"
    )

    APPDATA_FOLDER = Path(input("Enter ABSOLUTE PATH to your AppData folder: "))
    # Assume path it's good again, double profit $$

# If WWMI_FOLDER does not exist, tell user to fucking install it.
if not WWMI_FOLDER.exists():
    print(
        f"[ ! ] The folder {WWMI_FOLDER} does not exist.\n"
        "Please install the XXMI Launcher first.\n"
        "And fuck you.\n"
        "Here's the link smartypants: https://github.com/SpectrumQT/XXMI-Launcher"
    )
    exit(1)


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

from typing import  List, Tuple, TypedDict
from typing import TypedDict, List


# ────────────────────────────
#  Data shapes
# ────────────────────────────
class ModObject(TypedDict):
    name: str
    path: List[str]  # one or more folders (relative to SAVED_MODS_FOLDER)
    enabled: bool


type ModList = List[ModObject]


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

    if not ALLOWED_MODS_FILE.exists():
        ALLOWED_MODS_FILE.write_text('[]', encoding="utf-8")


# - ────────────────────────────
#  Folder validation
# - ────────────────────────────
def is_valid_mod_folder(folder: Path) -> Tuple[bool, str, List[Path]]:
    """
    Determine whether *folder* is a valid mod folder.

    Returns (status, representative_name, [paths_with_mod_ini])
    """

    output_fn = IOProvider().get_output()

    if not folder.is_dir():
        output_fn(f"\t[ ! ] {folder} is not a directory.")
        return (False, "", [])

    # Gather every directory that DIRECTLY contains a mod.ini file

    allowed_mods: List[str] = json.loads(ALLOWED_MODS_FILE.read_text(encoding="utf-8")) # Names of allowed mods (folder names)
    mod_dirs: List[Path] = [] # Keeps track of directories that contain a mod.ini file, the mods

    # Gather all .ini
    for p in folder.rglob("*.ini"):
        output_fn(f"\t[ / ] Found ini file: {p}")

        # If it's not a file, skip it
        if not p.is_file():
            continue

        file_name = p.name

        # If the directory it's already in captured, skip it
        if p.parent in mod_dirs:
            continue

        # If allowed but not in mod_dirs, add it
        if p.parent.name in allowed_mods and p.parent not in mod_dirs:
            mod_dirs.append(p.parent)

        # If current parent dir it's a subdir of an already allowed mod, skip it
        if any(p.parent.is_relative_to(allowed_mod) for allowed_mod in mod_dirs):
            output_fn(
                f"[ / ] Skipping '{p.parent.name}' as it is a subdirectory of an already allowed mod."
            )
            continue

        # If name it's "mod.ini" add it
        if file_name == "mod.ini":
            mod_dirs.append(p.parent)
            continue

        # Otherwise, ask user if they want to allow this mod
        positive_response = get_confirmation(
            f"Note: Allowing any .ini in this folder file will include the mod. \nFound ini file '{file_name}' in '{p.parent}'. Do you want to install this mod? (y/n): ",
            default="n"
        )

        if positive_response:
            allowed_mods.append(p.parent.name)  # Add the folder name to allowed_mods
            # Save updated allowed_mods
            with ALLOWED_MODS_FILE.open("w", encoding="utf-8") as fh:
                json.dump(allowed_mods, fh, indent=4, ensure_ascii=False)

            mod_dirs.append(p.parent)

            output_fn(
                f"[ + ] Allowed mod '{p.parent.name}'"
            )

    if not mod_dirs:
        # No mod.ini anywhere reachable ⇒ definitely NOT_MOD
        output_fn(f"\t[ ! ] No valid mod.ini found in {folder}.")
        return (False, "", [])

    # De-duplicate in case rglob found duplicates through symlinks
    mod_dirs = list(dict.fromkeys(mod_dirs))  # preserves order

    if len(mod_dirs) == 1:
        # Exactly one valid mod — name is that folder’s basename
        mod_root = mod_dirs[0]
        return (True, mod_root.name, [mod_root])

    # >1 distinct mod.ini-bearing folders ⇒ multi-mods
    # Use the *parent* folder’s name as representative label
    return (True, folder.name, mod_dirs)

