from typing import Callable
from handlers import *

def call_handler(
    name: str = "",
):
    # This is the handler summoner: it looks up the right handler by name and calls it, so you can trigger any action from anywhere (UI, web, tests).
    # Get handler function
    handler_fn = globals().get(f"{name}_handler")

    if handler_fn is None:
        raise ValueError(f"Handler '{name}' not found.")

    # Call the handler function with the provided input and output functions
    handler_fn()


"""
    Returns a lambda function that calls the call_handler with the given name.
"""
def get_handler(name: str) -> Callable[[], None]:
    # This is the handler vending machine: it gives you a callable for any handler by name, so you can build menus and UIs without hardcoding functions.
    return lambda: call_handler(name)
