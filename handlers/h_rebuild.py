from core import ACTIVE_MODS_FOLDER, SAVED_MODS_FOLDER, get_modlist, save_modlist, FolderValidation


def restore_entry_from_paths(
    modlist: ModList,
    paths_iter: Generator[Path, None, None],
    delete_invalid: bool = False,
    save: bool = True,  # If true, copy mod contents to SavedMods if not there already
) -> None:
    """
    Scan *paths_iter* for valid mods and ensure `modlist` contains them.

    EXTRA RULE (new):
        When adding or updating a mod we first check whether **any** of its
        folder paths are already referenced by another **multi-path** mod.
        If so, the new entry is *skipped* (or its conflicting paths are pruned)
        to avoid duplicated resources.
    """

    # helper: a live view of every path registered under a multi-path mod
    def _multipath_set(exclude: str | None = None) -> set[str]:
        return {
            p
            for m in modlist
            if len(m["path"]) > 1 and m["name"] != exclude
            for p in m["path"]
        }

    def _handle_mod_restore(name: str, path: str) -> None:
        # conflict check against existing multi-mods
        if path in _multipath_set():
            print(
                f"\t[ - ] Skipping {name}: "
                "its folder already belongs to another multi-path mod."
            )
            return

        existing = next((m for m in modlist if m["name"] == name), None)

        if existing:
            if existing["path"] != [path]:
                existing["path"] = [path]
                print(f"\t[ / ] Updated {name} paths.")
        else:
            modlist.append(ModObject(name=name, path=[path], enabled=False))
            print(f"\t[ + ] Added {name}.")

        if save and not (SAVED_MODS_FOLDER / name).exists():
            shutil.copytree(entry, SAVED_MODS_FOLDER / name)
            print(f"\t[ + ] Copied {name} to SavedMods folder.")

    for entry in paths_iter:
        # ─── reject plain files ─────────────────────────────────────────────
        if not entry.is_dir():
            if entry.is_file() and entry.name == "modlist.json":
                continue
            print(f"\t[ ! ] {entry.name} is not a directory and SHOULD NOT BE HERE")
            if delete_invalid:
                shutil.rmtree(entry, ignore_errors=True)
                print(f"\t[ + ] Deleted {entry.name}.")
            continue

        # ─── classify the candidate folder ─────────────────────────────────
        status, mod_name, mod_paths = is_valid_mod_folder(entry)

        if status == FolderValidation.NOT_MOD:
            print(f"\t[ ! ] {entry.name} is not a valid mod and SHOULD NOT BE HERE")
            if delete_invalid:
                shutil.rmtree(entry, ignore_errors=True)
                print(f"\t[ + ] Deleted {entry.name}.")
            continue

        # ─── Ensure no duplicate entries ────────────────────────────────
        if any(m["name"] == mod_name for m in modlist):
            # print(f"\t[ ! ] {mod_name} already exists in modlist.json, skipping.")
            continue

        # ─── SINGLE-MOD case ───────────────────────────────────────────────
        if status == FolderValidation.SINGLE_MOD:
            _handle_mod_restore(mod_name, str(mod_paths[0]))
            continue

        # ─── MULTI-MODS case ───────────────────────────────────────────────
        elif status == FolderValidation.MULTI_MODS:
            for path in mod_paths:
                mod_path = str(path)
                _handle_mod_restore(mod_name, mod_path)


def rebuild_handler(\
        delete_invalid: bool = False,  # If true, delete invalid mods and files
    ) -> None:
    """
    Create modlist.json from SavedMods folder or Mods folder.

    This is useful for the case in which either mod folder change outside of the manager,
    or the modlist.json gets corrupted.

    Also ensures there are no duplicate entries in modlist.json.
    Meaning mods that are present in other mods paths
    """

    print("- Rebuild modlist -".center(40, "="))
    print(
        "This will make sure all valid mods in SavedMods or Mods folder are registered in modlist.json."
    )
    print("\n\n")

    modlist = get_modlist()

    # Check if SavedMods folder has valid mods
    saved_mods = SAVED_MODS_FOLDER.glob("*")

    if any(saved_mods):
        restore_entry_from_paths(
            modlist, SAVED_MODS_FOLDER.glob("*"), delete_invalid=delete_invalid
        )

    active_mods = ACTIVE_MODS_FOLDER.glob("*")

    if any(active_mods):
        restore_entry_from_paths(
            modlist, ACTIVE_MODS_FOLDER.glob("*"), delete_invalid=delete_invalid
        )

    # collect every path that lives in a multi-path entry
    multi_paths: set[str] = {
        p for m in modlist if len(m["path"]) > 1 for p in m["path"]
    }

    # single-path mods to drop
    to_delete = {
        m["name"]
        for m in modlist
        if len(m["path"]) == 1 and m["path"][0] in multi_paths
    }

    for name in to_delete:
        print(f"\t[ - ] Removing {name} (path already covered by a multi-mod).")

    # mutate in place to keep external references valid
    modlist[:] = [m for m in modlist if m["name"] not in to_delete]

    save_modlist(modlist)
    print(f"[ + ] Restored mods from SavedMods and Mods folders.")

