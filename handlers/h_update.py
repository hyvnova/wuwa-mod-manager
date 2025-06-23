from pathlib import Path
from typing import Dict, List

from bananas import search
from bananas.shared import API_MOD_TYPE
from bisextypes import ModObject, TypeOfItem 
from core import get_modlist
from io_provider import IOProvider

# [REQUIRES OTHER HANDLERS]
from .h_download import _download_batch

def update_handler():
    """
    Goes thorugh each mod in the modlist,
    if can get the mod from gamebanana, update it.
    """

    input_fn, output_fn = IOProvider().get_io()

    modlist = get_modlist()
    if not modlist:
        output_fn("No mods to update.")
        return

    output_fn("[ / ] Checking for updates...")

    def _update_mod(mod: ModObject):
        """
        This function is the actual update process for a mod, like it does the handjob.
        Updates the mod from GameBanana and stores its resources.
        This function handles the update process for a mod.
        """
        output_fn(f"\t[ / ] Checking for updates: '{mod.name}' (ID: {mod.gb_id})...")

        # If no gamebanana id, try to search for the mod
        _mod: API_MOD_TYPE = None # type: ignore
        if not mod.gb_id:

            results = search.search_mod(mod.name, limit=3)

            if not results:
                output_fn(f"\t[ ! ] Could not find mod '{mod.name}' on GameBanana.")
                return

            output_fn(f"\t[ / ] Found {len(results)} potential matches:")
            for i, result in enumerate(results, 1):
                output_fn(f"\t[ {i} ] {result.name} (ID: {result.id})")
                output_fn(f"\t    Description: {result.description}")
                output_fn(f"\t    Author: {result.author}")
                output_fn(f"\t    Date: {result.date}")
                output_fn(f"\t    Downloads: {result.downloads}")

            output_fn(f"\n")
            try:
                choice = int(
                    input_fn(
                        "\t[ ? ] Select the mod you want to update (1-{len(results)}), or 0 to skip: "
                    )
                )
                if 1 <= choice <= len(results):
                    result = results[choice - 1]
                    mod.gb_id = int(result.id)  # type: ignore
                    _mod = result
                elif choice == 0:
                    output_fn(f"\t[ ! ] Skipping update for {mod.name}")
                    return
                else:
                    output_fn(f"\t[ ! ] Invalid choice. Skipping update for {mod.name}")
                    return
            except ValueError:
                output_fn(f"\t[ ! ] Invalid input. Skipping update for {mod.name}")
                return

        else:
            # Use the existing GameBanana ID to get the latest details
            output_fn(f"\t[ / ] Using existing GameBanana ID: {mod.gb_id}")
            _mod = search.get_mod_details(mod.gb_id)  # type: ignore
            if not _mod:
                output_fn(f"\t[ ! ] Could not get details for mod ID {mod.gb_id}")
                return

            # Show mod details and confirm update
            output_fn(f"\t[ / ] Found mod details:")
            output_fn(f"\t    Name: {_mod.name}")
            output_fn(f"\t    Description: {_mod.description}")
            output_fn(f"\t    Author: {_mod.author}")
            output_fn(f"\t    Date: {_mod.date}")
            output_fn(f"\t    Downloads: {_mod.downloads}")

            output_fn(f"\n")
            if input_fn("\t[ ? ] Update this mod? (y/n): ").lower() != "y":
                output_fn(f"\t[ ! ] Skipping update for {mod.name}")
                return

        # Now that we have the gamebanana id, we can update the mod
        details: Dict[str, List[Path]] = {}
        _download_batch([_mod], output_fn)
        validate_and_collect(details, DOWNLOADS_FOLDER / f"{_mod.name}.zip")

        modlist = get_modlist()

        # Add or update mods in the modlist
        for name, paths in details.items():

            # Check if the mod already exists in the modlist
            existing: ModObject = next((m for m in modlist if m.name == name and m.type == TypeOfItem.MOD), None)  # type: ignore
            str_paths = [str(p) for p in paths]

            if existing:
                if existing.path == str_paths:
                    output_fn(f"\t[ = ] {name} already present.")
                else:
                    output_fn(f"\t[ + ] Updating {name}")
                    existing.path = str_paths
                continue

            # Add new mod entry
            modlist.append(
                ModObject(name=name, path=str_paths, enabled=False, date=0, gb_id=None)
            )
            output_fn(f"\t[ + ] Updated {name}")

        save_modlist(modlist)

    # Go through each mod in the modlist and try to update it
    # This will try to find gamebanana id if not present
    # Then it will download the newest version of the mod
    import concurrent.futures

    def process_group(item):
        output_fn(f"\t[ / ] Updating group: {item.name}")
        with concurrent.futures.ThreadPoolExecutor() as executor:
            executor.map(_update_mod, item.members)  # type: ignore

    # with concurrent.futures.ThreadPoolExecutor() as executor:
    #     futures = []
    #     for item in modlist:
    #         if item.type == TypeOfItem.GROUP:
    #             futures.append(executor.submit(process_group, item))
    #         else:
    #             futures.append(executor.submit(_update_mod, item)) # type: ignore
    #     concurrent.futures.wait(futures)

    # Syncrhnoes version for testing
    for item in modlist:
        if item.type == TypeOfItem.GROUP:
            process_group(item)
        else:
            _update_mod(item) # type: ignore

    output_fn("[ + ] Update complete.")
