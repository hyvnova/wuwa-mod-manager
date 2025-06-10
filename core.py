from pathlib import Path
from bisextypes import GroupObject, TypeOfItem, ModList, ModObject, ModResource
from get_input import get_confirmation
from io_provider import IOProvider
import json
from typing import List, Tuple


from constants import *

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




# ----------------------------
#  JSON helpers
# ----------------------------
def get_modlist() -> ModList:
    # This loads the modlist from disk, and tries to recover if it's corrupted.
    if not MODLIST_FILE.exists():
        return []
    try:
        with MODLIST_FILE.open(encoding="utf-8") as fh:
            raw: list[dict] = json.load(fh)
    except (json.JSONDecodeError, OSError):
        print("[ ! ] Corrupted modlist, resetting.")
        save_modlist([])  # Reset modlist if corrupted
        return []

    out: ModList = []
    for item in raw:
        if not isinstance(item, dict) or "name" not in item:
            continue
        item_type = item.get("type", "mod")
        if item_type == TypeOfItem.GROUP.value:
            out.append(GroupObject.from_dict(item)) # type: ignore
        else:
            out.append(ModObject.from_dict(item)) # type: ignore
    return out


def save_modlist(modlist: ModList) -> None:
    # Save the modlist to disk, always as pretty JSON (for human debugging and cuteness).
    serializable = [m.to_dict() for m in modlist] # type: ignore
    with MODLIST_FILE.open("w", encoding="utf-8") as fh:
        json.dump(serializable, fh, indent=4, ensure_ascii=False)



def get_mod_resources() -> dict[str, ModResource]:
    # Loads mod resources (like thumbnails) from disk, with corruption recovery.
    if not MODS_RESOURCES_FILE.exists():
        return {}
    try:
        with MODS_RESOURCES_FILE.open(encoding="utf-8") as fh:
            raw: dict[str, dict] = json.load(fh)
    except (json.JSONDecodeError, OSError):
        print("[ ! ] Corrupted mods_resources.json, resetting.")
        save_mod_resources({})
        return {}

    return {name: ModResource.from_dict(data) for name, data in raw.items()}


def save_mod_resources(resources: dict[str, ModResource]) -> None:
    # Save mod resources to disk, always as pretty JSON.
    serializable = {name: res.to_dict() for name, res in resources.items()}
    with MODS_RESOURCES_FILE.open("w", encoding="utf-8") as fh:
        json.dump(serializable, fh, indent=4, ensure_ascii=False)


# ----------------------------
#  Boot-strapping
# ----------------------------
def ensure_dirs_and_files() -> None:
    # This is the boot ritual: make sure all folders and JSON files exist, so the app never crashes on startup.
    for directory in APP_DIRS:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True) # type: ignore
            print(f"[ + ] Created directory: {directory}")

    # Ensure all json files exist
    for json_file, init_content in APP_JSON_FILES:
        if not json_file.exists():
            json_file.write_text(init_content, encoding="utf-8")
            print(f"[ + ] Created JSON file: {json_file}")


# - ----------------------------
#  Folder validation
# - ----------------------------
def is_valid_mod_folder(folder: Path) -> Tuple[bool, str, List[Path]]:
    """
    This function is the bouncer for mod folders. It checks if a folder is a real mod, and asks the user if it's not sure.
    It also remembers allowed folders, so you don't get asked twice (unless you want to, you masochist).
    """

    output_fn = IOProvider().get_output()

    # if not folder.is_dir():
    #     output_fn(f"\t[ ! ] {folder} is not a directory.")
    #     return (False, "", [])

    # Gather every directory that DIRECTLY contains a mod.ini file

    allowed_mods: List[str] = json.loads(ALLOWED_MODS_FILE.read_text(encoding="utf-8")) # Names of allowed mods (folder names)
    mod_dirs: List[Path] = [] # Keeps track of directories that contain a mod.ini file, the mods

    # Gather all .ini
    for p in folder.rglob("*.ini"): # type: ignore
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

        output_fn("\n")

        # Otherwise, ask user if they want to allow this mod
        positive_response = get_confirmation(
            f"Note: Allowing any .ini in this folder file will include the mod. \nFound ini file '{file_name}' in '{p.parent.name}'. Do you want to install this mod? (y/n): ",
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
        # No mod.ini anywhere reachable ? definitely NOT_MOD
        output_fn(f"\t[ ! ] No valid mod.ini found in {folder}.")
        return (False, "", [])

    # De-duplicate in case rglob found duplicates through symlinks
    mod_dirs = list(dict.fromkeys(mod_dirs))  # preserves order

    if len(mod_dirs) == 1:
        # Exactly one valid mod - name is that folder's basename
        mod_root = mod_dirs[0]
        return (True, mod_root.name, [mod_root])

    # >1 distinct mod.ini-bearing folders ? multi-mods
    # Use the *parent* folder's name as representative label
    return (True, folder.name, mod_dirs)


def item_from_dict(d: dict) -> ModObject | GroupObject:
    # This is the shape-shifter: it builds the right object (mod or group) from a dict, so you never have to care.
    """
    Build a ModObject or GroupObject from a dictionary.
    """
    if d.get("type") == TypeOfItem.GROUP.value:
        return GroupObject.from_dict(d)
    else:
        return ModObject.from_dict(d)