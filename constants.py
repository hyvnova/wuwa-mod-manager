import os
from pathlib import Path
from typing import Tuple

# ----------------------------
#  Paths & constants
# ----------------------------
# All the important folders and files live here, so you only have to change things in one place if you move stuff around.
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
    Fetch all application directories from global constants.
    # Criteria:
    - Any variable that ends with `_FOLDER`.
    - Any variable that is a Path object.
    """
    return tuple(
        dir
        for dir in globals().values()
        if isinstance(dir, Path)  # Check if it's a Path object
        and dir.name.endswith("FOLDER") # Check if it ends with _FOLDER
    )


def get_app_json_files() -> Tuple[Tuple[Path, str], ...]:
    """
    Fetch all application JSON files from global constants.
    # Criteria:
    - Any variable that ends with `JSON`.
    - Any variable that is a Path object.

    If a variable in the format `INIT_OF_<file_name>` exists, it will be used as the initial content.
    Otherwise, "[]" will be used as the initial content.
    """

    return tuple(
        (
            file,  # path to the JSON file
            globals().get(f"INIT_OF_{file.name.upper()}", "[]") # try to find init content variable, default to "[]"
        )
        for file in globals().values()
        if isinstance(file, Path)  # Check if it's a Path object
        and file.name.endswith("JSON")  # Check if it ends with _JSON
    )