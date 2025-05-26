from pathlib import Path
import shutil
from core import ACTIVE_MODS_FOLDER, SAVED_MODS_FOLDER, ModObject, get_modlist, save_modlist
from get_input import get_menu_input


def _activate_mod(mod: ModObject) -> None:
    """
    Copy each folder listed in `mod["path"]` into ACTIVE_MODS_FOLDER/<modname>.
    """
    dest_root = ACTIVE_MODS_FOLDER / mod["name"]
    for p in mod["path"]:
        src = Path(p)
        if not src.is_absolute():
            src = SAVED_MODS_FOLDER / src
        if src.exists():
            shutil.copytree(src, dest_root / src.name, dirs_exist_ok=True)


def toggle_handler() -> None:
    """
    Toggle (enable ⇄ disable) selected mods.
    """

    modlist = get_modlist()
    if not modlist:
        print("No mods to toggle.")
        return go_back()

    sel = get_menu_input(
        prompt="Indexes to toggle (space-separated): ",
        zero_option_text="[ 0 ] All ",
        options=[m["name"] for m in modlist],
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
            print(f"\t[ + ] Enabled  {mod['name']}")
        else:
            shutil.rmtree(ACTIVE_MODS_FOLDER / mod["name"], ignore_errors=True)
            print(f"\t[ - ] Disabled {mod['name']}")

    save_modlist(modlist)
    go_back()
