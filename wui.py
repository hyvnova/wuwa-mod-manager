"""
Web User Interface (WUI) for the WuWa Mod Manager.
"""

import os
from pprint import pprint
import shutil
from typing import Any, List
import eel

from bisextypes import Action, GroupObject, Item, ModObject
from constants import WEBAPP_BUILD_PATH, WEBAPP_DIR_NAME, WEBAPP_PATH
from bisex import BiSex
from core import MODLIST_FILE, MODS_RESOURCES_FILE, item_from_dict, ensure_dirs_and_files, get_modlist, save_modlist
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

bisex = BiSex(
    py_types="bisextypes.py",  # whatever static types you keep
    js_types=WEBAPP_PATH / "src" / "lib" / "bisextypes.ts",
)


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
def py_perform_action(action: str, sel: List[dict[Any, Any]]) -> None:
    """
    Perform an action (e.g., toggle) on a selection of mod items.
    Args:
        action: The action to perform, as a string (e.g., "toggle").
        sel: A list of dicts representing selected items from the frontend.
    """
    IOProvider().set_io(
        input_fn=input_fn,
        output_fn=eel.js_output_fn,  # type: ignore
    )

    print = IOProvider().get_output()

    # Load the current modlist from file
    ml = get_modlist()

    # Convert the selection from dicts to Item objects
    selected: List[Item] = list(map(item_from_dict, sel))

    # Perform the requested action
    match Action.from_str(action):
        case Action.Toggle:
            # Toggle the 'enabled' state for each selected item
            for item in selected:
                try:
                    # Find the corresponding item in the modlist by equality
                    item_ref = ml[ml.index(item)]
                    item_ref.enabled = not item_ref.enabled
                except ValueError:
                    # Item not found in modlist; skip or log as needed
                    print(f"Item not found in modlist: {item}")

        case Action.Enable:
            # Enable all selected items
            for item in selected:
                try:
                    item_ref = ml[ml.index(item)]
                    item_ref.enabled = True
                except ValueError:
                    print(f"Item not found in modlist: {item}")

        case Action.Disable:
            # Disable all selected items
            for item in selected:
                try:
                    item_ref = ml[ml.index(item)]
                    item_ref.enabled = False
                except ValueError:
                    print(f"Item not found in modlist: {item}")

        case Action.Delete:
            # Remove selected items from modlist
            for item in selected:
                try:
                    ml.remove(item)
                except ValueError:
                    print(f"Item not found in modlist for deletion: {item}")

        case Action.Rename:
            # Rename item (assuming single selection for rename)
            if len(selected) == 1:
                item = selected[0]
                print(f"Renaming item: {item.name}")
                try:
                    item_ref = ml[ml.index(item)]
                    # Request new name from frontend
                    name = input_fn().strip() # Get input from JS and strip whitespace

                    if not name:
                        print("Rename action cancelled or empty name provided")
                        return

                    # Update the name of the item
                    item_ref.name = name
                    print(f"Item renamed to: {name}")

                except ValueError:
                    print(f"Item not found in modlist for rename: {item}")
            else:
                print("Rename action requires exactly one selected item")

        case Action.CreateGroup:
            # Create a group from selected ModObjects
            if len(selected) > 1:
                # Filter only ModObjects (can't group groups)
                mod_objects = [item for item in selected if isinstance(item, ModObject)]
                if mod_objects:
                    # Create new group
                    group_name = f"Group_{len([item for item in ml if isinstance(item, GroupObject)]) + 1}"
                    new_group = GroupObject(
                        name=group_name,
                        enabled=any(mod.enabled for mod in mod_objects),
                        members=mod_objects,
                    )

                    # Remove individual mods from modlist and add group
                    for mod in mod_objects:
                        try:
                            ml.remove(mod)
                        except ValueError:
                            pass
                    ml.append(new_group)
                else:
                    print("No valid ModObjects selected for grouping")
            else:
                print("Create group requires multiple selected items")

        case _:
            print(f"Unhandled action: {action}")

    # Save the updated modlist back to file
    save_modlist(ml)

    # Notify the frontend to update its modlist view
    with open(MODLIST_FILE, "r", encoding="utf-8") as f:
        data = f.read()
        eel.js_update_modlist(data)  # type: ignore

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
