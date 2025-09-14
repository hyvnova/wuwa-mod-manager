from pathlib import Path
import shutil
from sys import stderr
from typing import List
from core import (
    ACTIVE_MODS_FOLDER,
    SAVED_MODS_FOLDER,
    GroupObject,
    TypeOfItem,
    ModObject,
    get_modlist,
    save_modlist,
)
from get_input import get_menu_input
from io_provider import IOProvider


def _activate_mod(mod: ModObject) -> None:
    """Enable a mod by copying its folder(s) into the active mods folder."""
    dest_root = ACTIVE_MODS_FOLDER

    for p in mod.path:
        src = Path(p)

        # Should be always absolute, but just in case
        if not src.is_absolute():
            src = SAVED_MODS_FOLDER / src

        if src.exists():
            shutil.copytree(src, dest_root / src.name, dirs_exist_ok=True)
        else:
            IOProvider().get_output()(
                f"\t[ ! ] Source path {src} does not exist, cannot toggle."
            )

    IOProvider().get_output()(f"\t[ + ] Enabled  {mod.name}")


def _activate_group(group: GroupObject) -> None:
    """Enable all mods contained in a group."""
    output_fn = IOProvider().get_output()
    for mod in group.members:
        if not mod.enabled:
            mod.enabled = True
            _activate_mod(mod)

    output_fn(f"\t[ + ] Enabled  Group {group.name}")


def toggle_handler() -> None:
    """Toggle (enable/disable) selected mods or groups."""
    output_fn = IOProvider().get_output()

    modlist = get_modlist()
    if not modlist:
        output_fn("No mods to toggle.")
        return

    sel = get_menu_input(
        prompt="Indexes to toggle (space-separated): ",
        zero_option_text="[ 0 ] All ",
        options=[f"{['🔴', '🟢'][m.enabled]} | {m.name}" for m in modlist],
        space_separated=True,
    )
    sel = (sel,) if isinstance(sel, int) else sel
    targets = range(1, len(modlist) + 1) if 0 in sel else sel

    for idx in targets:
        if not (1 <= idx <= len(modlist)):
            continue

        item = modlist[idx - 1]
        item.enabled = not item.enabled

        if item.enabled:
            if item.type == TypeOfItem.GROUP:
                _activate_group(item)  # type: ignore[arg-type]
            elif item.type == TypeOfItem.MOD:
                _activate_mod(item)  # type: ignore[arg-type]
            else:
                stderr.write(f"Unimplemented item type {item.type} for {item.name}\n")
                exit(1)
        else:
            # Build list of paths to remove from Active Mods
            paths: List[Path]
            if item.type == TypeOfItem.GROUP:
                paths = [Path(p) for m in item.members for p in m.path]  # type: ignore[attr-defined]
            elif item.type == TypeOfItem.MOD:
                paths = [Path(p) for p in item.path]  # type: ignore[attr-defined]
            else:
                stderr.write(f"Unimplemented item type {item.type} for {item.name}\n")
                exit(1)

            for p in paths:
                shutil.rmtree(ACTIVE_MODS_FOLDER / p.name, ignore_errors=True)

            label = "Group " + item.name if item.type == TypeOfItem.GROUP else item.name
            output_fn(f"\t[ - ] Disabled {label}")

    save_modlist(modlist)
