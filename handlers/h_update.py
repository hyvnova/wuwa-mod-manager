from pathlib import Path
from bananas import search
from core import get_modlist
from io_provider import IOProvider


def update_handler():
    """
    Goes thorugh each mod in the modlist,
    if can get the mod from gamebanana, update it.
    """

    output_fn = IOProvider().get_output()

    modlist = get_modlist()
    if not modlist:
        output_fn("No mods to update.")
        return
    
    output_fn("[ / ] Checking for updates...")

    def _update_mod(mod):
        """
        Placeholder for the actual update logic.
        This function should handle the update process for a mod.
        """
        output_fn(f"\t[ + ] Updating mod '{mod['name']}' (ID: {mod['gamebanana_id']})...")

        # If no gamebanana id, try to search for the mod
        if not mod.get("gamebanana_id"):
            
            results = search.search_mod()


        else:   
            pass


    for mod in modlist:

        if mod.is_group:
            output_fn(f"\t[ / ] Updating group: {mod['name']}")

            map(
                _update_mod,
                (Path(p).name for p in mod["path"])
            )


        _update_mod(mod)