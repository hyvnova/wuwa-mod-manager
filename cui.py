"""
Console User Interface (CUI) – Rich Edition
Elegant, minimal, dark‑theme console UI with a purple accent.

Uses Rich for rendering, while keeping all handlers/UI I/O routed through
IOProvider for testability and Web UI reuse.
"""

# ────────────────────────────
#  Utilities
# ────────────────────────────
import os
import sys
from typing import Callable, Dict, List, Tuple
import re

from core import ensure_dirs_and_files
from handler_caller import get_handler
from io_provider import IOProvider
from str_util import most_similar_option

from rich.console import Console
from rich.theme import Theme
from rich.table import Table
from rich.panel import Panel
from rich import box
from rich.text import Text


# Theme: dark with purple accent
THEME = Theme(
    {
        "accent": "medium_purple3",
        "title": "bold plum1",
        "text": "white",
        "muted": "grey70",
        "success": "green3",
        "warning": "yellow3",
        "error": "red3",
    }
)
console = Console(theme=THEME)


# Route handlers’ output via Rich
def _styled_output(s: str) -> None:
    """Console output adapter that prettifies handler messages.

    Recognises common prefixes like "[ + ]", "[ ! ]", "[ / ]", "[ - ]"
    and renders them with Rich styles/symbols.
    Falls back to plain text for everything else.
    """
    if s is None:
        return
    line = str(s)
    if not line.strip():
        console.print("")
        return

    # Replace known banners with rules
    if "Rebuild modlist" in line:
        console.rule("[accent]Rebuild modlist[/accent]")
        return

    m = re.match(r"^\s*\[\s*([A-Z+\-\/=!]+)\s*\]\s*(.*)$", line)
    if m:
        tag, rest = m.group(1), m.group(2)
        tag = tag.upper()
        style = "text"
        symbol = "•"
        if tag in {"+"}:
            style, symbol = "success", "✓"
        elif tag in {"!", "FATAL"}:
            style, symbol = "error", "✖"
        elif tag in {"/"}:
            style, symbol = "accent", "»"
        elif tag in {"-"}:
            style, symbol = "warning", "–"
        elif tag in {"="}:
            style, symbol = "muted", "·"

        console.print(f"[{style}]{symbol}[/] {rest}")
        return

    console.print(line)


IOProvider().set_io(
    input_fn=console.input,  # preserves InputBuffer compatibility
    output_fn=_styled_output,
)


# ────────────────────────────
#  CLI menu
# ────────────────────────────
MENU: Dict[int, tuple[str, str, Callable[[], None]]] = {
    # Index: (Name, Description, Handler)
    0: ("Exit", "Close Program", lambda: sys.exit(0)),
    1: ("Install", "Install a mod from a local .zip file", get_handler("install")),
    2: ("Delete", "Remove mod from modlist and move it to Deleted Mods", get_handler("delete")),
    3: ("Toggle", "Enable/Disable a mod or group", get_handler("toggle")),
    4: ("List", "List all tracked mods", get_handler("list")),
    5: ("Create Group", "Group mods to toggle as one", get_handler("group")),
    6: ("Rebuild", "Re-scan folders and fix modlist", get_handler("rebuild")),
    7: ("Download", "Fetch mods from GameBanana (beta)", get_handler("download")),
    8: ("Update", "Update installed mods (beta)", get_handler("update")),
}


def _render_header() -> None:
    console.print(Panel.fit("[title]Hyvnt’s[/title] [accent]WuWa Mod Manager[/accent]", border_style="accent"))


def _render_menu() -> Tuple[List[str], dict[int, tuple[str, str, Callable[[], None]]]]:
    # Prepare entries in a stable order by index
    entries = {k: v for k, v in sorted(MENU.items(), key=lambda kv: kv[0])}

    table = Table(
        title="[muted]Main Menu[/muted]",
        box=box.ROUNDED,
        show_lines=False,
        header_style="accent",
        expand=False,
    )
    table.add_column("Idx", justify="right", style="muted", no_wrap=True)
    table.add_column("Action", style="text")
    table.add_column("Description", style="muted")

    for idx, (name, desc, _) in entries.items():
        accent_name = f"[accent]{name}[/accent]" if idx != 0 else name
        table.add_row(f"{idx}", accent_name, desc)

    console.print(table)

    option_names = [name.lower() for (name, _, _) in entries.values()]
    return option_names, entries


def _ask_choice(option_names: List[str]) -> int | None:
    # Prompt user (supports number or fuzzy name)
    choice = console.input("\n[accent]›[/accent] Number / name ([muted]q to quit[/muted]): ").strip()
    if choice.lower() == "q":
        sys.exit(0)

    if choice.isdigit():
        return int(choice)

    match = most_similar_option(choice, option_names)
    if not match:
        console.print("[warning]No match. Try again.[/warning]")
        return None
    return option_names.index(match)


def main() -> None:
    ensure_dirs_and_files()
    # Rebuild modlist.json on startup (no output if already consistent)
    get_handler("rebuild")()

    while True:
        console.clear()
        _render_header()
        option_names, entries = _render_menu()

        idx = _ask_choice(option_names)
        if idx is None or idx not in entries:
            continue

        console.rule("[accent]Running[/accent]")
        try:
            entries[idx][-1]()
        except KeyboardInterrupt:
            console.print("\n[warning]Interrupted[/warning]")
        except SystemExit:
            raise
        except Exception as exc:  # noqa: BLE001
            console.print(f"[error]Error:[/error] {exc}")

        console.rule()
        console.input("[muted]Press Enter to continue…[/muted]")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[warning]Interrupted, bye.[/warning]")
