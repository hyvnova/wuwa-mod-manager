from typing import Callable
from handlers import *  # noqa: F401,F403 - dynamic lookup by name


def call_handler(name: str = "") -> None:
    """Dynamically locate and invoke a handler by its short name.

    Given a name like "install", this looks for a callable named
    "install_handler" within the imported handlers and executes it.
    """
    handler_fn = globals().get(f"{name}_handler")
    if handler_fn is None:
        raise ValueError(f"Handler '{name}' not found.")
    handler_fn()


def get_handler(name: str) -> Callable[[], None]:
    """Return a thunk that calls the named handler when invoked."""
    return lambda: call_handler(name)
