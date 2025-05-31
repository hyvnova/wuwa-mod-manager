from re import S
import shutil

from io_provider import IOProvider
from core import ACTIVE_MODS_FOLDER, DELETED_MODS_FOLDER, SAVED_MODS_FOLDER, get_modlist, save_modlist
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
        options=[m.name for m in modlist],
        space_separated=True,
    )
    sel = (sel,) if isinstance(sel, int) else sel

    if 0 in sel:
        
        for d in (SAVED_MODS_FOLDER, ACTIVE_MODS_FOLDER):
            shutil.move(d, DELETED_MODS_FOLDER / d.name)
            shutil.rmtree(d, ignore_errors=True)

        modlist.clear()
    else:
        for idx in sel:
            if 1 <= idx <= len(modlist):
                mod = modlist[idx - 1]

                # move mod to DELETED_MODS_FOLDER if it exists
                try:
                    if (SAVED_MODS_FOLDER / mod.name).exists():
                        output_fn(f"\t[ / ] Attempting to move '{ SAVED_MODS_FOLDER / mod.name }' to {DELETED_MODS_FOLDER / mod.name }")
                        shutil.move(SAVED_MODS_FOLDER / mod.name,  DELETED_MODS_FOLDER / mod.name)
                    else:
                        output_fn(f"\t[ / ] Attempting to move '{ ACTIVE_MODS_FOLDER / mod.name }' to {DELETED_MODS_FOLDER / mod.name }")
                        shutil.move(ACTIVE_MODS_FOLDER / mod.name, DELETED_MODS_FOLDER / mod.name)

                except Exception as e:
                    output_fn(f"\t[ ! ] '{mod.name}' could not be moved to deleted mods: {e}")

                shutil.rmtree(SAVED_MODS_FOLDER / mod.name, ignore_errors=True)
                shutil.rmtree(ACTIVE_MODS_FOLDER / mod.name, ignore_errors=True)
                modlist.remove(mod)

                output_fn(f"\t[ + ] Deleted {mod.name}.")

    output_fn("\n[ + ] Deletion complete.")
    save_modlist(modlist)
