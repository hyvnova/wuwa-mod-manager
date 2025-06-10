"""
Web User Interface (WUI) for the WuWa Mod Manager.
"""

# This file is the magical bridge between Python and the Svelte frontend.
# It exposes backend logic to the browser, so your mods can be managed with style (and less pain).

import os
from pathlib import Path
from pprint import pprint
import shutil
from typing import Any, List
import eel

from bisextypes import Action, GroupObject, Item, ModObject, TypeOfItem
from constants import ACTIVE_MODS_FOLDER, DELETED_MODS_FOLDER, SAVED_MODS_FOLDER, WEBAPP_BUILD_PATH, WEBAPP_DIR_NAME, WEBAPP_PATH
from bisex import BiSex
from core import MODLIST_FILE, MODS_RESOURCES_FILE, item_from_dict, ensure_dirs_and_files, get_modlist, save_modlist
from handler_caller import call_handler
from input_buffer import InputBuffer
from io_provider import IOProvider
from handlers import *

# Default setup for IOProvider
IOProvider().set_io(
    input_fn=lambda: "No input provided",
    output_fn=pprint,  # Default to Pprint for output
)

# Not an expert, but I'm using a list because python uses references with them which means PROFIT $$$ GOLD GOLD GOLD
waiting_for_input = [False]
recieved_input = ["No input recieved"]

# BiSex is the type wizard: it keeps Python and TypeScript types in sync, so you never have to guess what an Item is.
bisex = BiSex(
    py_types="bisextypes.py",  # whatever static types you keep
    js_types=WEBAPP_PATH / "src" / "lib" / "bisextypes.ts",
)


@eel.expose
@bisex.raw_fuck("EelService")  
def py_get_input(value: str) -> None:
    """
    This is the callback JS calls when the user gives input in the browser.
    It unblocks the Python-side input loop, so the backend can keep going.
    """
    # print(f"Received input from JS: {value}")
    
    # Set the value and stop waiting for input
    recieved_input[0] = value
    waiting_for_input[0] = False

def input_fn() -> str:
    # This function is called when Python needs input from the user, but we're in a browser!
    # So we poke JS, then sleep until JS pokes us back (see above).
    # It's a little dance, but it works.
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
def py_perform_action(action: str, sel: List[dict[Any, Any]]) -> None:
    """
    This is the main entrypoint for mod actions from the frontend.
    It takes a string action and a list of selected items, and does the right thing.
    """
    # IOProvider is set to use the web input/output, so all prompts go to the browser.
    IOProvider().set_io(
        input_fn=input_fn,
        output_fn=eel.js_output_fn,  # type: ignore
    )

    print = IOProvider().get_output()

    # Validate input
    if not sel:
        print("No items selected for action")
        return

    # Load the current modlist from file
    ml = get_modlist()

    # Convert the selection from dicts to Item objects
    selected: List[Item] = list(map(item_from_dict, sel))

    # Get indices of selected items in modlist
    indices = []
    for item in selected:
        try:
            idx = ml.index(item) + 1  # +1 because handlers use 1-based indexing
            indices.append(idx)
        except ValueError:
            print(f"Item not found in modlist: {item}")
            continue

    if not indices:
        return

    # Convert indices to space-separated string for handlers
    indices_str = " ".join(map(str, indices))

    # Map frontend actions to handler names
    handler_map = {
        Action.Toggle: "toggle",
        Action.Enable: "toggle",  # Enable is handled by toggle handler
        Action.Disable: "toggle",  # Disable is handled by toggle handler
        Action.Delete: "delete",
        Action.Rename: "rename",
        Action.CreateGroup: "group",
    }

    try:
        # Get the handler name for this action
        action_enum = Action.from_str(action)
        handler_name = handler_map[action_enum]

        # Special handling for rename action
        if action_enum == Action.Rename:
            if len(selected) != 1:
                print("Rename action requires exactly one selected item")
                return
            
            # Get new name from frontend
            name = input_fn().strip()
            if not name:
                print("Rename action cancelled or empty name provided")
                return

            # Check if name already exists
            if any(m.name == name for m in ml if m != selected[0]):
                print(f"Name '{name}' is already in use")
                return

            # Push both the index and the new name to the input buffer
            InputBuffer().push(indices_str, name)
        else:
            # For other actions, just push the indices
            InputBuffer().push(indices_str)
        
        # Call the appropriate handler
        call_handler(handler_name)

    except (KeyError, ValueError) as e:
        print(f"Invalid action or handler not found: {e}")
        return

    # Notify the frontend to update its modlist view
    try:
        with open(MODLIST_FILE, "r", encoding="utf-8") as f:
            data = f.read()
            eel.js_update_modlist(data)  # type: ignore
    except Exception as e:
        print(f"Failed to update frontend: {e}")

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
    This lets the frontend call any handler by name (like 'install', 'delete', etc).
    It's a little dangerous, but very flexible. (Validation is minimal, so be careful!)
    """
    # Some nasty validation to make sure handler_name exists, THIS IS A CRIME
    handler_name = handler_name.strip().lower().replace(" ", "_")

    if handler_name == "exit":
        quit(1)

    print(f"Calling handler: {handler_name}")

    # Handler function it's already imported from handlers modula as "{handler_name}_handler"
    handler_fn = globals().get(f"{handler_name}_handler")

    # print all globals that have handler in their name
    for name, value in globals().items():
        if "handler" in name:
            print(f"Found handler: {name}")

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
# This is the startup ritual: make sure all folders/files exist, sync types, and clean up old builds.
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
