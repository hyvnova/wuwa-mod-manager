"""
Web User Interface (WUI) for the WuWa Mod Manager.
"""

import os
import shutil
from typing import List
import eel


from bisextypes import Action, Item, TypeOfItem
from constants import WEBAPP_BUILD_PATH, WEBAPP_DIR_NAME, WEBAPP_PATH
from bisex import BiSex
from core import MOD_RES_FOLDER, MODLIST_FILE, MODS_RESOURCES_FILE, ModList, ModResource, ensure_dirs_and_files, get_mod_resources, get_modlist
from io_provider import IOProvider
from handlers import *


# Not an expert, but I'm using a list because python uses references with them which means PROFIT $$$ GOLD GOLD GOLD
waiting_for_input = [True]
recieved_input = ["No input recieved"]

bisex = BiSex(
    py_types="bisextypes.py",  # whatever static types you keep
    js_types=WEBAPP_PATH / "src" / "lib" / "bisextypes.ts",
)

@eel.expose
@bisex.raw_fuck("EelService")
def py_perform_action(action: Action, selected: List[Item]) -> None:
    pass

@eel.expose
@bisex.raw_fuck("EelService")  
def py_get_input(value: str) -> None:
    """
    Expose a Python function to the Svelte frontend.
    This function will be called from JS to send input back to Python.
    """
    # print(f"Received input from JS: {value}")
    
    # Set the value and stop waiting for input
    recieved_input[0] = value
    waiting_for_input[0] = False

def input_fn() -> str:
    # tell js we want input
    eel.js_request_input() # type: ignore

    # zZzZzzZ
    waiting_for_input[0] = True

    # wait until we got that fent
    while waiting_for_input[0]:
        eel.sleep(1) 
    
    # return the value we got
    value = recieved_input[0]
    recieved_input[0] = "No input recieved"  # Reset for next input

    # print(f"Returning input: {value}")
    return value


@eel.expose
@bisex.raw_fuck("EelService")
def py_raw_get_modlist() -> str:
    with open(MODLIST_FILE, "r", encoding="utf-8") as f:
        return f.read()


@eel.expose
@bisex.raw_fuck("EelService")

def py_raw_get_mod_resources() -> str:
    with open(MODS_RESOURCES_FILE, "r", encoding="utf-8") as f:
        return f.read()


@eel.expose
@bisex.raw_fuck("EelService")
def py_call_handler(handler_name: str) -> None:
    """
    Expose a Python function to the Svelte frontend.
    This function will call the specified handler.
    """

    # Some nasty validation to make sure handler_name exists, THIS IS A CRIME
    handler_name = handler_name.strip().lower().replace(" ", "_")

    if handler_name == "exit":
        quit(1)

    print(f"Calling handler: {handler_name}")

    # Handler function it's already imported from handlers modula as "{handler_name}_handler"
    handler_fn = globals().get(f"{handler_name}_handler")

    # print(f"{handler_fn=}")

    if handler_fn is None:
        raise ValueError(f"Handler '{handler_name}' not found.")

    # print(f"{eel.js_input_fn=}")
    # print(f"{eel.js_output_fn=}")

    # It's kinda bad to set functions in every fucking call
    # But I can't be bothered to do it better right now
    # Fuck you.
    IOProvider().set_io(
        input_fn=input_fn,
        output_fn=eel.js_output_fn, # type: ignore
    )

    handler_fn()

# INIT ---------------------------------------------------
ensure_dirs_and_files()

bisex.perform()

# delete build directory if it exists
if WEBAPP_BUILD_PATH.exists():
    shutil.rmtree(WEBAPP_BUILD_PATH)

# build svelte app
os.system(f"cd {WEBAPP_DIR_NAME} && npm run build")

eel.init(
    str(WEBAPP_BUILD_PATH),
    # svelte build
    allowed_extensions=[".js", ".html", ".ts", ".svelte"],
)

eel.start("index.html", mode="edge")
