from core import get_modlist
from cui_core.shared import get_menu_input, go_back
from handlers import delete_handler 

def cui_delete_handler() -> None:
    """
    Removes selected mods entirely (files & entry).
    """

    modlist = get_modlist()

    if not modlist:
        print("Nothing to delete.")
        return

    sel = get_menu_input(
        prompt="Indexes to delete: ",
        zero_option_text="[ 0 ] All ",
        options=[m["name"] for m in modlist],
        space_separated=True,
    )
    
    delete_handler(sel)
    go_back()
