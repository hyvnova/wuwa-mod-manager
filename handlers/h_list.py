from core import get_modlist
from io_provider import IOProvider


def list_handler() -> None:
    """
    Prints a BEAUTIFUL table of installed mods.
    Each mod has an index, name, and status (enabled/disabled).
    """

    output_fn = IOProvider().get_output()

    modlist = get_modlist()

    if not modlist:
        output_fn("No mods installed. If there are mods in the SavedMods folder, run 'Rebuild' to add them.")
        return

    # Settings for column widths
    idx_col_w = 4  # For "[ 12 ]"
    name_col_w = max(12, max(len(m.name) for m in modlist))  # At least 12 wide
    status_col_w = len("Enabled") + 2  # a little breathing room
    total_w = idx_col_w + name_col_w + status_col_w + 10  # spacing + dividers

    # Header
    output_fn(" Installed mods ".center(total_w, "="))
    # Table headers
    output_fn(
        f"{'Idx'.center(idx_col_w)} | "
        f"{'Mod Name'.center(name_col_w)} | "
        f"{'Status'.center(status_col_w)}"
    )
    output_fn("-" * total_w)

    for idx, m in enumerate(modlist, 1):
        status = ["🔴", "🟢"][m.enabled]
        output_fn(
            f"{str(idx).center(idx_col_w)} | "
            f"{m.name.center(name_col_w)} | "
            f"{status.center(status_col_w)}"
        )

    output_fn("=" * total_w)
