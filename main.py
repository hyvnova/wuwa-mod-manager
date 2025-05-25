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


def is_valid_mod_folder(folder: Path) -> Tuple[FolderValidation, Dict[str, List[Path]]]:
    """
    Recursively look for folders containing a *.ini.

    Returns:
        status, {mod_name: [folder, ...]}
    """
    if not folder.is_dir():
        return FolderValidation.NOT_MOD, {}

    if any((folder / f).is_file() for f in folder.glob("*.ini")):
        return FolderValidation.SINGLE_MOD, {folder.name: [folder]}

    collected: Dict[str, List[Path]] = {}
    for sub in folder.iterdir():
        if not sub.is_dir():
            continue
        status, child = is_valid_mod_folder(sub)
        if status is not FolderValidation.NOT_MOD:
            # merge
            for k, v in child.items():
                collected.setdefault(k, []).extend(v)

    if not collected:
        return FolderValidation.NOT_MOD, {}
    if len(collected) == 1:
        return FolderValidation.SINGLE_MOD, collected
    return FolderValidation.MULTI_MODS, collected


def validate_and_collect(into: Dict[str, List[Path]], zip_file: Path) -> None:
    """Extract zip → validate → populate `into` dict (mod_name -> [paths])"""
    print(f"\t[ / ] Checking {zip_file.name}")

    if not extract_zip(zip_file, SAVED_MODS_FOLDER):
        return

    root = SAVED_MODS_FOLDER / zip_file.stem
    status, mods = is_valid_mod_folder(root)
    if status is FolderValidation.NOT_MOD:
        print(f"\t[ ! ] {zip_file.name} isn't a mod, discarding.")
        shutil.rmtree(root, ignore_errors=True)
        return

    into.update(mods)


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

    chosen: Dict[str, List[Path]] = {}
    if sel == 0:
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

    if sel == 0:
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

    • Disabled mods → enabled  (copies files in)
    • Enabled  mods → disabled (removes files)

    User can pick multiple indexes or 0 for "toggle ALL".
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

    targets = range(1, len(modlist) + 1) if sel == 0 else sel

    for idx in targets:
        if not (1 <= idx <= len(modlist)):
            continue

        mod = modlist[idx - 1]
        new_state = not mod["enabled"]
        mod["enabled"] = new_state

        if new_state:
            _activate_mod(mod)
            print(f"\t[ + ] Enabled  {mod['name']}")
        else:
            shutil.rmtree(ACTIVE_MODS_FOLDER / mod["name"], ignore_errors=True)
            print(f"\t[ - ] Disabled {mod['name']}")

    save_modlist(modlist)
    go_back()


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


def group_handler() -> None:
    """
    Combine several installed mods into a single “meta-mod” entry.

    • The new group inherits the *union* of all selected mods’ paths.
    • The original individual entries are removed.
    • The group is added *disabled* so the user can toggle it later.
    """

    print("- Create a group -".center(40, "="))
    print(
        "This will create a group of mods, allowing you to toggle them all at once.\n"
    )

    modlist: ModList = get_modlist()
    if not modlist:
        print("No mods installed.")
        return go_back()

    # ── choose members ──────────────────────────────────────────
    sel = get_menu_input(
        prompt="Indexes of mods to group (space-separated): ",
        zero_option_text="[ 0 ] Auto make group by name similarity",
        options=[m["name"] for m in modlist],
        space_separated=True,
    )

    if sel == 0:
        # selected_mods: ModList = modlist[:]  # copy
        print("Auto-selecting mods by name similarity…")
        # todo! # this is a placeholder, implement auto-selection logic
        selected_mods = []
    else:
        selected_mods = [modlist[idx - 1] for idx in sel if 1 <= idx <= len(modlist)]

    if not selected_mods:
        print("No valid mods selected.")
        return go_back()

    # ── choose a unique group name ─────────────────────────────

    group_name: str = ""
    while True:
        try:
            print("\t - You can use format 'groupname-modname' to create an exclusive group.")
            print("\t - Exclusive groups will only allow one mod under the group to be enabled at a time.")

            group_name = input(
                "Group name (leave empty to auto-generate): "
            ).strip().lower()

            if not group_name:
                # Auto-generate a group name based on selected mods
                group_name = "-".join(
                    sorted(set(m["name"] for m in selected_mods))
                )
                print(f"Auto-generated group name: '{group_name}'")

            break

        except KeyboardInterrupt:
            print("\nInterrupted, going back.")
            return go_back()

        except Exception as e:
            print("[ ! ] That is not a valid name.")
            continue

    if any(m["name"] == group_name for m in modlist):
        print(f"A mod or group called '{group_name}' already exists.")
        return go_back()

    # ── build path list (deduplicated, keeps order) ────────────
    group_paths: List[str] = []
    seen: set[str] = set()
    for mod in selected_mods:
        for p in mod["path"]:
            if p not in seen:
                seen.add(p)
                group_paths.append(p)

    # ── drop originals & append new group ──────────────────────
    modlist = [m for m in modlist if m not in selected_mods]
    modlist.append(
        ModObject(
            name=group_name,
            path=group_paths,
            enabled=False,  # groups start disabled
        )
    )

    save_modlist(modlist)
    print(f"\t[ + ] Created group '{group_name}' with {len(selected_mods)} mods.")

    return go_back()


def restore_entry_from_paths(
    modlist: ModList,
    paths_iter: Generator[Path, None, None],
    delete_invalid: bool = False,
    save: bool = True,  # If true, will copy mod contents to saved mods folder if doesn't already exist
):

    for entry in paths_iter:
        if not entry.is_dir():
            print(f"\t[ ! ] {entry.name} is not a directory and SHOULD NOT BE HERE")

            if delete_invalid:
                # If user wants to delete invalid mods, remove the folder
                shutil.rmtree(entry, ignore_errors=True)
                print(f"\t[ + ] Deleted {entry.name}.")

            continue

        status, mods = is_valid_mod_folder(entry)

        if status == FolderValidation.NOT_MOD:
            # If the folder is not a mod, we skip it
            print(f"\t[ ! ] {entry.name} is not a valid mod and SHOULD NOT BE HERE")

            if delete_invalid:
                # If user wants to delete invalid mods, remove the folder
                shutil.rmtree(entry, ignore_errors=True)
                print(f"\t[ + ] Deleted {entry.name}.")

            continue

        # ============================================================================================
        # -- Whether we find a single mod or multiple mods, we will add them to the modlist
        # -- if they don't already exist.
        # -- if they exists, they will be updated with the new paths.

        elif status == FolderValidation.SINGLE_MOD:
            mod_name = entry.name
            if not any(
                m["name"] == mod_name for m in modlist
            ):  # If mod doesn't already exist

                # Add the mod to the modlist
                modlist.append(
                    ModObject(name=mod_name, path=[str(entry)], enabled=False)
                )
                print(f"\t[ + ] Added {mod_name}.")

            else:
                # If  paths are different, update the existing mod
                existing_mod = next(m for m in modlist if m["name"] == mod_name)
                if existing_mod["path"] != [str(entry)]:
                    existing_mod["path"] = [str(entry)]
                    print(f"\t[ / ] Updated {mod_name} paths.")

            # Save the mod to the SavedMods folder if it doesn't already exist
            if save and not (SAVED_MODS_FOLDER / mod_name).exists():
                shutil.copytree(entry, SAVED_MODS_FOLDER / mod_name)
                print(f"\t[ + ] Copied {mod_name} to SavedMods folder.")

        elif status == FolderValidation.MULTI_MODS:
            for mod_name, paths in mods.items():

                if not any(
                    m["name"] == mod_name for m in modlist
                ):  # If mod doesn't already exist
                    modlist.append(
                        ModObject(
                            name=mod_name, path=[str(p) for p in paths], enabled=False
                        )
                    )
                    print(f"\t[ + ] Added {mod_name}.")

                # If mod already exists, update the paths
                else:
                    existing_mod = next(m for m in modlist if m["name"] == mod_name)
                    if existing_mod["path"] != [str(p) for p in paths]:
                        existing_mod["path"] = [str(p) for p in paths]
                        print(f"\t[ / ] Updated {mod_name} paths.")

                # Save the mod to the SavedMods folder if it doesn't already exist
                if save and not (SAVED_MODS_FOLDER / mod_name).exists():
                    shutil.copytree(entry, SAVED_MODS_FOLDER / mod_name)
                    print(f"\t[ + ] Copied {mod_name} to SavedMods folder.")


def rebuild_handler() -> None:
    """
    Create modlist.json from SavedMods folder or Mods folder.

    This is useful for the case in which either mod folder change outside of the manager,
    or the modlist.json gets corrupted.
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

    print(f"[ + ] Restored mods from SavedMods and Mods folders.")
    save_modlist(modlist)

    return go_back()


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
