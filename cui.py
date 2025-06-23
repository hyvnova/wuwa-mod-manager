"""
Console User Interface (CUI) for WuWa mod manager
"""  


# ────────────────────────────
#  Utilities
# ────────────────────────────
import os
import sys
from typing import Callable, Dict
from core import ensure_dirs_and_files
from handler_caller import get_handler
from input_buffer import InputBuffer
from io_provider import IOProvider
from str_util import most_similar_option


IOProvider().set_io(
    input_fn=input,
    output_fn=print,
)

# InputBuffer().push("8")

# ────────────────────────────
#  CLI loop
# ────────────────────────────
MENU: Dict[int, tuple[str, str, Callable[[], None]]] = {
    0: ("Exit", "Close Program", lambda: sys.exit(0)),
    1: ("Install", "Install a mod from a local .zip file", get_handler("install")),
    2: ("Delete", "Remove mod from modlist and move it to Deleted Mods Folder", get_handler("delete")),
    3: ("Toggle", "Toggle a mod", get_handler("toggle")),
    4: ("List", "List all tracked mods", get_handler("list")),
    5: ("Create Group", "Makes selected mods act as one", get_handler("group")),
    6: ("Rebuild", "Rebuild the mod list to reflect changes in the Mods folder", get_handler("rebuild")),
    7: ("Download", "Download a mod from gamebanana (BETA)", get_handler("download")),
    8: ("Update", "Update a mod from gamebanana (BETA)", get_handler("update")),
}


def main() -> None:
    ensure_dirs_and_files()
    get_handler("rebuild")()  # Rebuild modlist.json on startup


    input_fn, print_fn = IOProvider().get_io()

    option_names = [name.lower() for name, _, _ in MENU.values()]

    while True:
        os.system("cls" if os.name == "nt" else "clear")

        print_fn("WuWa Mod Manager".center(30, "="))

        for i, n in enumerate(option_names):
            print_fn(f"[ {i} ] {n} - {MENU[i][1]}")


        choice = input_fn("\nNumber / name (q to quit): ").strip()
        if choice.lower() == "q":
            sys.exit(0)

        # translate choice -> index
        if choice.isdigit():
            idx = int(choice)
        else:
            match = most_similar_option(choice, option_names)
            if not match:
               continue

            idx = option_names.index(match)

        if idx not in MENU:
            print_fn("Invalid selection.")
            continue

        print_fn("\n")
        MENU[idx][-1]()
        # wait for user to press Enter before continuing
        input_fn("\nPress Enter to continue...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted, bye.")