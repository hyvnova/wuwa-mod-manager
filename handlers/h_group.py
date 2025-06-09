from typing import Callable, List

from io_provider import IOProvider
from core import GroupObject, TypeOfItem, ModList, ModObject, get_modlist, save_modlist
from get_input import get_menu_input


def group_handler() -> None:
    """
    Combine several installed mods into a single “meta-mod” entry.
    """

    (input_fn, output_fn) = IOProvider().get_io()

    output_fn("- Create a group -".center(40, "="))
    output_fn(
        "This will create a group of mods, allowing you to toggle them all at once.\n"
    )

    modlist: ModList = get_modlist()
    if not modlist:
        output_fn("No mods installed.")
        return

    sel = get_menu_input(
        prompt="Indexes of mods to group (space-separated): ",
        zero_option_text="[ 0 ] Auto make group by name similarity",
        options=[m.name for m in modlist if m.type == TypeOfItem.MOD],
        space_separated=True,
    )
    sel = (sel,) if isinstance(sel, int) else sel

    if 0 in sel:
        # placeholder for future smart-group logic
        output_fn("Auto-select not implemented yet.")
        return

    selected_mods: List[ModObject] = [modlist[idx - 1] for idx in sel if 1 <= idx <= len(modlist)] # type: ignore

    if not selected_mods:
        output_fn("No valid mods selected.")
        return

    output_fn("\n")
    output_fn("- Selected -".center(20, " "))
    for idx, m in enumerate(selected_mods, 1):
        output_fn(f"[ {idx} ] {m.name}")

    output_fn("---------------------------------------")

    # ------------- group name -------------
    while True:

        output_fn("Enter a name for the group: (leave empty to auto-generate)")
        group_name = input_fn().strip().lower()
        if not group_name:
            group_name = "-".join(sorted(set(m.name for m in selected_mods)))
            output_fn(f"Auto-generated group name: '{group_name}'")
        if any(m.name == group_name for m in modlist):
            output_fn(f"'{group_name}' already exists.")
            continue
        break

    # # ------------- paths dedupe -----------
    # group_paths: List[str] = []
    # seen: set[str] = set()
    # for m in selected_mods:
    #     for p in m["path"]:
    #         if p not in seen:
    #             seen.add(p)
    #             group_paths.append(p)

    # ------------- commit -----------------
    modlist = [m for m in modlist if m not in selected_mods]
    modlist.append(
        GroupObject(
            name=group_name,
            enabled=False,
            members=selected_mods,
        )
    )
    save_modlist(modlist)

    output_fn(f"\t[ + ] Created group '{group_name}' with {len(selected_mods)} mods.")
