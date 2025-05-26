"""
Web User Interface (WUI) for the WuWa Mod Manager.
"""

import os
import eel
from pathlib import Path
import importlib

SVELTE_PATH = Path(__file__).parent / "wui"

from handlers import *

@eel.expose
def call_handler(handler_name: str) -> None:
    """
    Expose a Python function to the Svelte frontend.
    This function will call the specified handler.
    """
    
    print(f"Calling handler: {handler_name}")

    # Handler function it's already imported from handlers modula as "{handler_name}_handler"
    handler_fn = globals().get(f"{handler_name}_handler")

    print(f"{handler_fn=}")

    if handler_fn is None:
        raise ValueError(f"Handler '{handler_name}' not found.")
    
    print(f"{eel.js_input_fn=}")
    print(f"{eel.js_output_fn=}")

    handler_fn(
        eel.js_input_fn,
        eel.js_output_fn,
    )

# build svelte app
os.system("cd wui && npm run build")

eel.init(
    str(SVELTE_PATH / "build"),
    # svelte build
    allowed_extensions=[".js", ".html", ".ts", ".svelte"],
)

eel.start("index.html", mode="edge")
