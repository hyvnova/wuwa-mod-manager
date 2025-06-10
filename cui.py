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


# ────────────────────────────
#  CLI loop
# ────────────────────────────
MENU: Dict[int, tuple[str, Callable[[], None]]] = {
    0: ("Exit", lambda: sys.exit(0)),
    1: ("Install", get_handler("install")),
    2: ("Delete", get_handler("delete")),
    3: ("Toggle", get_handler("toggle")),
    4: ("List", get_handler("list")),
    5: ("Create Group", get_handler("group")),
    6: ("Rebuild", get_handler("rebuild")),
    7: ("Download", get_handler("download")),
    8: ("Update", get_handler("update")),
}


def main() -> None:
    ensure_dirs_and_files()
    get_handler("rebuild")()  # Rebuild modlist.json on startup


    option_names = [name.lower() for name, _ in MENU.values()]

    while True:
        os.system("cls" if os.name == "nt" else "clear")

        print("WuWa Mod Manager".center(30, "="))

        for i, n in enumerate(option_names):
            print(f"[ {i} ] {n}")

        choice = input("\nNumber / name (q to quit): ").strip()
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
            print("Invalid selection.")
            continue

        print("\n")
        MENU[idx][1]()
        # wait for user to press Enter before continuing
        input("\nPress Enter to continue...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted, bye.")