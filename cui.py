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
from cui_core.shared import go_back
from handlers import *
from str_sort import sort_by_similitude


    
    
# ────────────────────────────
#  CLI loop
# ────────────────────────────
MENU: Dict[int, tuple[str, Callable[[], None]]] = {
    0: ("Exit", lambda: sys.exit(0)),
    1: ("Install", install_handler),
    2: ("Delete", delete_handler),
    3: ("Toggle", toggle_handler),  # ← merged Enable/Disable
    4: ("List", list_handler),
    5: ("Create Group", group_handler),
    6: ("Rebuild", rebuild_handler),
}


def main() -> None:
    ensure_directories()
    rebuild_handler()  # Rebuild modlist.json on startup

    option_names = [name.lower() for name, _ in MENU.values()]

    while True:
        os.system("cls" if os.name == "nt" else "clear")

        print("\nWuWa Mod Manager".center(30, "="))

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
            go_back()
            continue

        print("\n")
        MENU[idx][1]()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted, bye.")