from typing import Callable
from handlers import *

def call_handler(
    name: str = "",
):
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
    return lambda: call_handler(name)
