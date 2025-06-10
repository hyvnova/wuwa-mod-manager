import os
from pathlib import Path

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

# Not the smartest way I guess
APP_DIRS = (
    TEMP_FOLDER,
    SAVED_MODS_FOLDER,
    ACTIVE_MODS_FOLDER,
    DELETED_MODS_FOLDER,
    MOD_RES_FOLDER,
)

MODLIST_FILE = (
    WWMI_FOLDER / "modlist.json"
)  # File where the list of installed mods and groups are stored

# Allowed folder names. Since some mods don't contain a mod.ini and intead have something like "modname.ini"
# This file will keep track of the allowed folder names, so that the user can install mods without a mod.ini file.
ALLOWED_MODS_FILE = WWMI_FOLDER / "allowed_mods.json"

# UI resources for mods
MODS_RESOURCES_FILE = (
    WWMI_FOLDER / "mods_resources.json"
)  # File where the resources for the mods are stored


# Path var: Initial Content
APP_JSON_FILES = (
    (MODLIST_FILE, "[]"),
    (ALLOWED_MODS_FILE, "[]"),
    (MODS_RESOURCES_FILE, "{}"),
)


# ---------------------------- Webapp Paths & Contants ----------------------------
# All the webapp paths live here, so the backend and frontend can always find each other (and you can move the webapp if you want).
# This will assume the webapp directory is in the same directory as this script.
WEBAPP_DIR_NAME = "webapp"
WEBAPP_PATH = Path(__file__).parent / WEBAPP_DIR_NAME
WEBAPP_BUILD_PATH = WEBAPP_PATH / "build"