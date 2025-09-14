import os
from pathlib import Path
from typing import Tuple

"""
Constants and path helpers for the WuWa Mod Manager.

This module centralizes all filesystem locations used by the application and
provides helpers to enumerate app directories and JSON files in a robust way.

Design goals:
- Keep all path configuration in one place.
- Offer programmatic discovery of app directories and JSON files so
  bootstrapping code can create them when missing.
"""

# ----------------------------
#  Paths & constants
# ----------------------------
# All the important folders and files live here, so you only have to change
# things in one place if you move stuff around.
USER_HOME = Path.home()

APPDATA_FOLDER = Path(os.getenv("APPDATA", USER_HOME / "AppData" / "Roaming"))
WWMI_FOLDER = APPDATA_FOLDER / "XXMI Launcher" / "WWMI"  # XXMI Mod Installer folder

DOWNLOADS_FOLDER = USER_HOME / "Downloads"
TEMP_FOLDER = (
    DOWNLOADS_FOLDER / "_HWWMM_TEMP"
)  # Temporary folder for storing shit like stupid mod id because this stupid system can't handle that

SAVED_MODS_FOLDER = (
    WWMI_FOLDER / "SavedMods"
)  # Folder where mods are saved after installation
ACTIVE_MODS_FOLDER = (
    WWMI_FOLDER / "Mods"
)  # Folder where active mods are copied to be used by the game
DELETED_MODS_FOLDER = (
    WWMI_FOLDER / "DeletedMods"
)  # Folder where deleted mods are moved to, so that they can be restored later
MOD_RES_FOLDER = (
    WWMI_FOLDER / "ModResources"
)  # Folder where UI resources are stored, images or icons


MODLIST_JSON = (
    WWMI_FOLDER / "modlist.json"
)  # File where the list of installed mods and groups are stored
INIT_OF_MODLIST_JSON = "[]"

# Allowed folder names. Since some mods don't contain a mod.ini and intead have something like "modname.ini"
# This file will keep track of the allowed folder names, so that the user can install mods without a mod.ini file.
ALLOWED_MODS_FILE = WWMI_FOLDER / "allowed_mods.json"
INIT_OF_ALLOWED_MODS_FILE = "[]"

# UI resources for mods
MODS_RESOURCES_FILE = (
    WWMI_FOLDER / "mods_resources.json"
)  # File where the resources for the mods are stored
INIT_OF_MODS_RESOURCES_FILE = "{}"  # Initial content of the mods resources file


# ---------------------------- Webapp Paths & Contants ----------------------------
# All the webapp paths live here, so the backend and frontend can always find each other (and you can move the webapp if you want).
# This will assume the webapp directory is in the same directory as this script.
WEBAPP_DIR_NAME = "webapp"
WEBAPP_PATH = Path(__file__).parent / WEBAPP_DIR_NAME
WEBAPP_BUILD_PATH = WEBAPP_PATH / "build"


# ---------------------------- Helper Functions / Public API ----------------------------
def get_app_dirs() -> tuple[Path, ...]:
    """
    Return all application directories declared in this module.

    Selection criteria (by variable name):
    - Variable name ends with "_FOLDER".
    - Variable value is a Path instance.

    This inspects the module's globals using both name and value to avoid
    mistakes caused by checking the final path segment (which is unrelated to
    the constant's name).
    """
    items: list[Path] = []
    for name, value in globals().items():
        if name.endswith("_FOLDER") and isinstance(value, Path):
            items.append(value)
    return tuple(items)


def get_app_json_files() -> Tuple[Tuple[Path, str], ...]:
    """
    Return all JSON files to be created/ensured by the application.

    Selection criteria:
    - Variable value is a Path whose suffix is ".json" (case-insensitive).

    Initial contents selection:
    - Look for a sibling constant named `INIT_OF_<VAR_NAME>` where VAR_NAME
      is the name of the Path constant (e.g., `MODLIST_JSON`).
    - If not found, default to "[]" (a valid empty JSON array).
    """
    out: list[tuple[Path, str]] = []
    for name, value in globals().items():
        if isinstance(value, Path) and value.suffix.lower() == ".json":
            init_var = f"INIT_OF_{name}"
            init = globals().get(init_var, "[]")
            out.append((value, init))
    return tuple(out)
