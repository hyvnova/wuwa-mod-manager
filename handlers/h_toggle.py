from pathlib import Path
import shutil
from core import ACTIVE_MODS_FOLDER, SAVED_MODS_FOLDER, ModObject, get_modlist, save_modlist
from get_input import get_menu_input
from io_provider import IOProvider


def _activate_mod(mod: ModObject) -> None:
    """
    Copy each path in the mod to the active mods folder.
    """
    dest_root = ACTIVE_MODS_FOLDER
    for p in mod["path"]:
        src = Path(p)

        # Should be always absolute, but just in case
        if not src.is_absolute():
            src = SAVED_MODS_FOLDER / src

        
        if src.exists():
            shutil.copytree(src, dest_root / src.name, dirs_exist_ok=True)
        else:
            IOProvider().get_output()(f"\t[ ! ] Source path {src} does not exist, cannot toggle.")


def toggle_handler() -> None:
    """
    Toggle (enable ⇄ disable) selected mods.
    """
    output_fn = IOProvider().get_output()

    modlist = get_modlist()
    if not modlist:
        output_fn("No mods to toggle.")
        return

    sel = get_menu_input(
        prompt="Indexes to toggle (space-separated): ",
        zero_option_text="[ 0 ] All ",
        options=[f"{['🔴', '🟢'][m['enabled']]} | {m["name"]}" for m in modlist],
        space_separated=True,
    )
    sel = (sel,) if isinstance(sel, int) else sel
    targets = range(1, len(modlist) + 1) if 0 in sel else sel

    for idx in targets:
        if not (1 <= idx <= len(modlist)):
            continue

        mod = modlist[idx - 1]
        mod["enabled"] = not mod["enabled"]

        if mod["enabled"]:
            _activate_mod(mod)
            output_fn(f"\t[ + ] Enabled  {mod['name']}")
        else:
            # Remove the mod from the active mods folder
            for p in mod["path"]:
                shutil.rmtree(ACTIVE_MODS_FOLDER / Path(p).name, ignore_errors=True)
            output_fn(f"\t[ - ] Disabled {mod['name']}")

    save_modlist(modlist)
