"""
Web User Interface (WUI) for the WuWa Mod Manager.
"""

import os
import shutil
import eel
from pathlib import Path

from io_provider import IOProvider

SVELTE_PATH = Path(__file__).parent / "wui"

from handlers import *


# Not an expect, but I'm assing a list because python uses references with them which means PROFIT $$$ GOLD GOLD GOLD
waiting_for_input = [True]
recieved_input = ["No input recieved"]

@eel.expose
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
    eel.js_request_input()

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
def call_handler(handler_name: str) -> None:
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
        output_fn=eel.js_output_fn,
    )

    handler_fn()

# delete build directory if it exists
if (SVELTE_PATH / "build").exists():
    shutil.rmtree(SVELTE_PATH / "build")


# build svelte app
os.system("cd wui && npm run build")

eel.init(
    str(SVELTE_PATH / "build"),
    # svelte build
    allowed_extensions=[".js", ".html", ".ts", ".svelte"],
)

eel.start("index.html", mode="edge")
