from core import get_modlist, save_modlist
from io_provider import IOProvider



def rename_handler() -> None:
    """
    Renames an installed mod.
    Prompts for the mod index and new name.
    """
    output_fn = IOProvider().get_output()
    input_fn = IOProvider().get_input()

    modlist = get_modlist()

    if not modlist:
        output_fn("No mods installed. If there are mods in the SavedMods folder, run 'Rebuild' to add them.")
        return

    # Print mod list for reference
    output_fn("\nInstalled mods:")
    for idx, m in enumerate(modlist, 1):
        output_fn(f"{idx}. {m.name}")

    # Get mod index
    while True:
        try:
            output_fn("Enter the number of the mod to rename (0 to cancel): ")
            idx = int(input_fn())
            if idx == 0:
                return
            if 1 <= idx <= len(modlist):
                break
            output_fn("Invalid index. Please try again.")
        except ValueError:
            output_fn("Please enter a valid number.")

    mod = modlist[idx - 1]
    
    # Get new name
    while True:
        output_fn(f"Enter new name for '{mod.name}' (or press Enter to cancel): ")
        new_name = input_fn().strip()
        if not new_name:
            return
        if new_name == mod.name:
            output_fn("New name is the same as current name. Please enter a different name.")
            continue
        if any(m.name == new_name for m in modlist):
            output_fn("A mod with this name already exists. Please choose a different name.")
            continue
        break

    # Perform rename
    try:
        old_name = mod.name
        mod.name = new_name
        output_fn(f"Successfully renamed '{old_name}' to '{new_name}'")
    except Exception as e:
        output_fn(f"Failed to rename mod: {str(e)}") 

    # save modlist
    save_modlist(modlist)