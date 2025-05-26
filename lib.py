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

import enum
import json
import os
import shutil
import sys
import zipfile
from pathlib import Path
from typing import Callable, Dict, Generator, List, Tuple, TypedDict

from click import group
from ezstools.string_tools import sort_by_similitude
from get_input import get_confirmation, get_menu_input

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


ModList = List[ModObject]


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
        d.mkdir(parents=True, exist_ok=True)
    if not MODLIST_FILE.exists():
        MODLIST_FILE.write_text("[]", encoding="utf-8")


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
class FolderValidation(enum.Enum):
    NOT_MOD = 0
    SINGLE_MOD = 1
    MULTI_MODS = 2


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
            return (
                FolderValidation.SINGLE_MOD,
                root.name,
                [root]
            )
        
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


# ────────────────────────────
#  Utilities
# ────────────────────────────
def go_back() -> None:
    input("\nPress <Enter> to return to the menu…")


def _activate_mod(mod: ModObject) -> None:
    """
    Copy each folder listed in `mod["path"]` into ACTIVE_MODS_FOLDER/<modname>.
    """
    dest_root = ACTIVE_MODS_FOLDER / mod["name"]
    for p in mod["path"]:
        src = Path(p)
        if not src.is_absolute():
            src = SAVED_MODS_FOLDER / src
        if src.exists():
            shutil.copytree(src, dest_root / src.name, dirs_exist_ok=True)


# ────────────────────────────
#  Handlers
# ────────────────────────────
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

def delete_handler() -> None:
    """
    Removes selected mods entirely (files & entry).
    """

    modlist = get_modlist()
    if not modlist:
        print("Nothing to delete.")
        return go_back()

    sel = get_menu_input(
        prompt="Indexes to delete: ",
        zero_option_text="[ 0 ] All ",
        options=[m["name"] for m in modlist],
        space_separated=True,
    )
    sel = (sel,) if isinstance(sel, int) else sel

    if 0 in sel:
        for d in (SAVED_MODS_FOLDER, ACTIVE_MODS_FOLDER):
            shutil.rmtree(d, ignore_errors=True)
        modlist.clear()
    else:
        for idx in sel:
            if 1 <= idx <= len(modlist):
                mod = modlist[idx - 1]
                shutil.rmtree(SAVED_MODS_FOLDER / mod["name"], ignore_errors=True)
                shutil.rmtree(ACTIVE_MODS_FOLDER / mod["name"], ignore_errors=True)
                modlist.remove(mod)

    save_modlist(modlist)
    go_back()

def toggle_handler() -> None:
    """
    Toggle (enable ⇄ disable) selected mods.
    """

    modlist = get_modlist()
    if not modlist:
        print("No mods to toggle.")
        return go_back()

    sel = get_menu_input(
        prompt="Indexes to toggle (space-separated): ",
        zero_option_text="[ 0 ] All ",
        options=[m["name"] for m in modlist],
        space_separated=True,
    )
    sel = (sel,) if isinstance(sel, int) else sel
    targets = range(1, len(modlist) + 1) if 0 in sel else sel

    for idx in targets:
        if not (1 <= idx <= len(modlist)):
            continue

        mod = modlist[idx - 1]
        mod["enabled"] = not mod["enabled"]

        if mod["enabled"]:
            _activate_mod(mod)
            print(f"\t[ + ] Enabled  {mod['name']}")
        else:
            shutil.rmtree(ACTIVE_MODS_FOLDER / mod["name"], ignore_errors=True)
            print(f"\t[ - ] Disabled {mod['name']}")

    save_modlist(modlist)
    go_back()


def group_handler() -> None:
    """
    Combine several installed mods into a single “meta-mod” entry.
    """

    print("- Create a group -".center(40, "="))
    print(
        "This will create a group of mods, allowing you to toggle them all at once.\n"
    )

    modlist: ModList = get_modlist()
    if not modlist:
        print("No mods installed.")
        return go_back()

    sel = get_menu_input(
        prompt="Indexes of mods to group (space-separated): ",
        zero_option_text="[ 0 ] Auto make group by name similarity",
        options=[m["name"] for m in modlist],
        space_separated=True,
    )
    sel = (sel,) if isinstance(sel, int) else sel

    if 0 in sel:
        # placeholder for future smart-group logic
        print("Auto-select not implemented yet.")
        return go_back()

    selected_mods = [modlist[idx - 1] for idx in sel if 1 <= idx <= len(modlist)]
    if not selected_mods:
        print("No valid mods selected.")
        return go_back()
    
    print("\n")
    print("- Selected -".center(20, " "))
    for idx, m in enumerate(selected_mods, 1):
        print(f"[ {idx} ] {m['name']}")

    print("\n")

    # ------------- group name -------------
    while True:
        group_name = (
            input("Group name (leave empty to auto-generate): ").strip().lower()
        )
        if not group_name:
            group_name = "-".join(sorted(set(m["name"] for m in selected_mods)))
            print(f"Auto-generated group name: '{group_name}'")
        if any(m["name"] == group_name for m in modlist):
            print(f"'{group_name}' already exists.")
            continue
        break

    # ------------- paths dedupe -----------
    group_paths: List[str] = []
    seen: set[str] = set()
    for m in selected_mods:
        for p in m["path"]:
            if p not in seen:
                seen.add(p)
                group_paths.append(p)

    # ------------- commit -----------------
    modlist = [m for m in modlist if m not in selected_mods]
    modlist.append(ModObject(name=group_name, path=group_paths, enabled=False))
    save_modlist(modlist)

    print(f"\t[ + ] Created group '{group_name}' with {len(selected_mods)} mods.")
    go_back()


def restore_entry_from_paths(
    modlist: ModList,
    paths_iter: Generator[Path, None, None],
    delete_invalid: bool = False,
    save: bool = True,  # If true, copy mod contents to SavedMods if not there already
) -> None:
    """
    Scan *paths_iter* for valid mods and ensure `modlist` contains them.

    EXTRA RULE (new):
        When adding or updating a mod we first check whether **any** of its
        folder paths are already referenced by another **multi-path** mod.
        If so, the new entry is *skipped* (or its conflicting paths are pruned)
        to avoid duplicated resources.
    """

    # helper: a live view of every path registered under a multi-path mod
    def _multipath_set(exclude: str | None = None) -> set[str]:
        return {
            p
            for m in modlist
            if len(m["path"]) > 1 and m["name"] != exclude
            for p in m["path"]
        }

    def _handle_mod_restore(name: str, path: str) -> None:
        # conflict check against existing multi-mods
        if path in _multipath_set():
            print(
                f"\t[ - ] Skipping {name}: "
                "its folder already belongs to another multi-path mod."
            )
            return

        existing = next((m for m in modlist if m["name"] == name), None)
        
        if existing:
            if existing["path"] != [path]:
                existing["path"] = [path]
                print(f"\t[ / ] Updated {name} paths.")
        else:
            modlist.append(ModObject(name=name, path=[path], enabled=False))
            print(f"\t[ + ] Added {name}.")

        if save and not (SAVED_MODS_FOLDER / name).exists():
            shutil.copytree(entry, SAVED_MODS_FOLDER / name)
            print(f"\t[ + ] Copied {name} to SavedMods folder.")

    for entry in paths_iter:
        # ─── reject plain files ─────────────────────────────────────────────
        if not entry.is_dir():
            if entry.is_file() and entry.name == "modlist.json":
                continue
            print(f"\t[ ! ] {entry.name} is not a directory and SHOULD NOT BE HERE")
            if delete_invalid:
                shutil.rmtree(entry, ignore_errors=True)
                print(f"\t[ + ] Deleted {entry.name}.")
            continue

        # ─── classify the candidate folder ─────────────────────────────────
        status, mod_name, mod_paths = is_valid_mod_folder(entry)

        if status == FolderValidation.NOT_MOD:
            print(f"\t[ ! ] {entry.name} is not a valid mod and SHOULD NOT BE HERE")
            if delete_invalid:
                shutil.rmtree(entry, ignore_errors=True)
                print(f"\t[ + ] Deleted {entry.name}.")
            continue

        # ─── Ensure no duplicate entries ────────────────────────────────
        if any(m["name"] == mod_name for m in modlist):
            # print(f"\t[ ! ] {mod_name} already exists in modlist.json, skipping.")
            continue

        # ─── SINGLE-MOD case ───────────────────────────────────────────────
        if status == FolderValidation.SINGLE_MOD:
            _handle_mod_restore(mod_name, str(mod_paths[0]))
            continue

        # ─── MULTI-MODS case ───────────────────────────────────────────────
        elif status == FolderValidation.MULTI_MODS:
            for path in mod_paths:
                mod_path = str(path)
                _handle_mod_restore(mod_name, mod_path)


def rebuild_handler() -> None:
    """
    Create modlist.json from SavedMods folder or Mods folder.

    This is useful for the case in which either mod folder change outside of the manager,
    or the modlist.json gets corrupted.

    Also ensures there are no duplicate entries in modlist.json.
    Meaning mods that are present in other mods paths
    """

    print("- Rebuild modlist -".center(40, "="))
    print(
        "This will make sure all valid mods in SavedMods or Mods folder are registered in modlist.json."
    )
    print("\n\n")

    modlist = get_modlist()

    delete_invalid = get_confirmation(
        "Do you want to delete invalid mods and files? (y/n): ",
        default="n",
    )

    # Check if SavedMods folder has valid mods
    saved_mods = SAVED_MODS_FOLDER.glob("*")

    if any(saved_mods):
        restore_entry_from_paths(
            modlist, SAVED_MODS_FOLDER.glob("*"), delete_invalid=delete_invalid
        )

    active_mods = ACTIVE_MODS_FOLDER.glob("*")

    if any(active_mods):
        restore_entry_from_paths(
            modlist, ACTIVE_MODS_FOLDER.glob("*"), delete_invalid=delete_invalid
        )

    # collect every path that lives in a multi-path entry
    multi_paths: set[str] = {
        p for m in modlist if len(m["path"]) > 1 for p in m["path"]
    }

    # single-path mods to drop
    to_delete = {m["name"] for m in modlist if len(m["path"]) == 1 and m["path"][0] in multi_paths}

    for name in to_delete:
        print(f"\t[ - ] Removing {name} (path already covered by a multi-mod).")

    # mutate in place to keep external references valid
    modlist[:] = [m for m in modlist if m["name"] not in to_delete]

    save_modlist(modlist)
    print(f"[ + ] Restored mods from SavedMods and Mods folders.")

    return go_back()


def list_handler() -> None:
    """
    Prints a BEAUTIFUL table of installed mods.
    Each mod has an index, name, and status (enabled/disabled).
    """

    modlist = get_modlist()
    if not modlist:
        print("No mods installed.")
        return go_back()

    # Settings for column widths
    idx_col_w = 4  # For "[ 12 ]"
    name_col_w = max(12, max(len(m["name"]) for m in modlist))  # At least 12 wide
    status_col_w = len("Enabled") + 2  # a little breathing room
    total_w = idx_col_w + name_col_w + status_col_w + 10  # spacing + dividers

    # Header
    print("- Installed mods -".center(total_w, "="))
    # Table headers
    print(
        f"{'Idx'.center(idx_col_w)} | "
        f"{'Mod Name'.center(name_col_w)} | "
        f"{'Status'.center(status_col_w)}"
    )
    print("-" * total_w)

    for idx, m in enumerate(modlist, 1):
        status = "Enabled" if m["enabled"] else "Disabled"
        print(
            f"{str(idx).center(idx_col_w)} | "
            f"{m['name'].center(name_col_w)} | "
            f"{status.center(status_col_w)}"
        )
    print("=" * total_w)
    go_back()


# ────────────────────────────
#  CLI loop
# ────────────────────────────
MENU: Dict[int, tuple[str, Callable[[], None]]] = {
    0: ("Exit", lambda: sys.exit(0)),
    1: ("Install", install_handler),
    2: ("Delete", delete_handler),
    3: ("Toggle", toggle_handler),  # ← merged Enable/Disable
    4: ("List", list_handler),
    5: ("Create Group", group_handler),
    6: ("Rebuild", rebuild_handler),
}


def main() -> None:
    ensure_directories()
    rebuild_handler()  # Rebuild modlist.json on startup

    option_names = [name.lower() for name, _ in MENU.values()]

    while True:
        os.system("cls" if os.name == "nt" else "clear")

        print("\nWuWa Mod Manager".center(30, "="))

        for i, n in enumerate(option_names):
            print(f"[ {i} ] {n}")

        choice = input("\nNumber / name (q to quit): ").strip()
        if choice.lower() == "q":
            sys.exit(0)

        # translate choice -> index
        if choice.isdigit():
            idx = int(choice)
        else:
            match = sort_by_similitude(choice, option_names, case_sensitive=False)[-1]
            idx = option_names.index(match)

        if idx not in MENU:
            print("Invalid selection.")
            go_back()
            continue

        print("\n")
        MENU[idx][1]()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted, bye.")
