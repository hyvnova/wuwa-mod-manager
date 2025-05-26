def group_handler() -> None:
    """
    Combine several installed mods into a single “meta-mod” entry.
    """

    print("- Create a group -".center(40, "="))
    print(
        "This will create a group of mods, allowing you to toggle them all at once.\n"
    )

    modlist: ModList = get_modlist()
    if not modlist:
        print("No mods installed.")
        return go_back()

    sel = get_menu_input(
        prompt="Indexes of mods to group (space-separated): ",
        zero_option_text="[ 0 ] Auto make group by name similarity",
        options=[m["name"] for m in modlist],
        space_separated=True,
    )
    sel = (sel,) if isinstance(sel, int) else sel

    if 0 in sel:
        # placeholder for future smart-group logic
        print("Auto-select not implemented yet.")
        return go_back()

    selected_mods = [modlist[idx - 1] for idx in sel if 1 <= idx <= len(modlist)]
    if not selected_mods:
        print("No valid mods selected.")
        return go_back()

    print("\n")
    print("- Selected -".center(20, " "))
    for idx, m in enumerate(selected_mods, 1):
        print(f"[ {idx} ] {m['name']}")

    print("\n")

    # ------------- group name -------------
    while True:
        group_name = (
            input("Group name (leave empty to auto-generate): ").strip().lower()
        )
        if not group_name:
            group_name = "-".join(sorted(set(m["name"] for m in selected_mods)))
            print(f"Auto-generated group name: '{group_name}'")
        if any(m["name"] == group_name for m in modlist):
            print(f"'{group_name}' already exists.")
            continue
        break

    # ------------- paths dedupe -----------
    group_paths: List[str] = []
    seen: set[str] = set()
    for m in selected_mods:
        for p in m["path"]:
            if p not in seen:
                seen.add(p)
                group_paths.append(p)

    # ------------- commit -----------------
    modlist = [m for m in modlist if m not in selected_mods]
    modlist.append(ModObject(name=group_name, path=group_paths, enabled=False))
    save_modlist(modlist)

    print(f"\t[ + ] Created group '{group_name}' with {len(selected_mods)} mods.")
    go_back()
