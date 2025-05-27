"""
Console User Interface (CUI) for WuWa mod manager
"""  


# ────────────────────────────
#  Utilities
# ────────────────────────────
import os
import sys
from typing import Callable, Dict
from core import ensure_directories
from handler_caller import get_handler
from io_provider import IOProvider
from str_sort import sort_by_similitude


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
    5: ("Create Group", get_handler("create_group")),
    6: ("Rebuild", get_handler("rebuild")),
}


def main() -> None:
    ensure_directories()
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
            match = sort_by_similitude(choice, option_names, case_sensitive=False)[-1]
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