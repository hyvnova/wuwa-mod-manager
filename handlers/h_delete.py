import shutil

from io_provider import IOProvider
from core import ACTIVE_MODS_FOLDER, SAVED_MODS_FOLDER, get_modlist, save_modlist
from get_input import get_menu_input


def delete_handler(
) -> None:
    """
    Removes selected mods entirely (files & entry).
    """

    output_fn = IOProvider().get_output()

    modlist = get_modlist()
    if not modlist:
        output_fn("Nothing to delete.")
        return

    sel = get_menu_input(
        prompt="Indexes to delete: ",
        zero_option_text="[ 0 ] All ",
        options=[m["name"] for m in modlist],
        space_separated=True,
    )
    sel = (sel,) if isinstance(sel, int) else sel

    if 0 in sel:
        for d in (SAVED_MODS_FOLDER, ACTIVE_MODS_FOLDER):
            shutil.rmtree(d, ignore_errors=True)
        modlist.clear()
    else:
        for idx in sel:
            if 1 <= idx <= len(modlist):
                mod = modlist[idx - 1]
                shutil.rmtree(SAVED_MODS_FOLDER / mod["name"], ignore_errors=True)
                shutil.rmtree(ACTIVE_MODS_FOLDER / mod["name"], ignore_errors=True)
                modlist.remove(mod)

    save_modlist(modlist)
