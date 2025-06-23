import sys
from typing import List, Tuple, Union
from io_provider import IOProvider
from str_util import most_similar_option

def get_menu_input(
    zero_option_text: str,
    prompt: str,
    options: List[str],
    space_separated: bool = False,
) -> Union[int, Tuple[int, ...]]:
    """
    Ask the user to pick from *options*.
    The caller decides whether multiple picks are allowed (``space_separated``).

    • If the user types **numbers** → those numbers are taken as 1-based indexes
      (0 is the special "zero option").
    • If the user types **text** → we fuzzy-match each token against the option list
      with ``most_similar_option`` and take the closest hit.

    Returns
    -------
    int
        a single index (when ``space_separated=False``)
    tuple[int, ...]
        many indexes in input order with duplicates removed

    # This is the menu fairy: it lets users pick options by number or by typing (even badly), so the UI is always friendly and forgiving.
    """

    (input_fn, output_fn) = IOProvider().get_io()

    output_fn(zero_option_text)
    for idx, opt in enumerate(options, start=1):
        output_fn(f"[ {idx} ]\t{opt}")

    def _match_token(token: str) -> int | None:
        """Return 1-based index for a textual token (best fuzzy match)"""
        token = token.strip().lower()

        if not token:
            return None

        best = most_similar_option(token, options)

        if not best:
            return None
        
        _best_for_display = best.split("|")[1] if "|" in best else best

        print(f"Best match for '{token}' is '{_best_for_display}' which is option {options.index(best) + 1}")
        return options.index(best) + 1 if best in options else None

    while True:
        output_fn("\n")
        raw = input_fn(prompt)
        
        if not raw:
            output_fn("That's not it.")
            continue

        # Split once if multi-select, otherwise keep as single token
        tokens = raw.split() if space_separated else [raw]

        indices: List[int] = []
        for tok in tokens:
            if tok.isdigit():
                num = int(tok)
                if 0 <= num <= len(options):
                    indices.append(num)
                else:
                    output_fn(f"\t[ ! ] {num} is out of range and will be ignored.")
            else:
                match = _match_token(tok)
                if match is None:
                    output_fn(f"\t[ ! ] '{tok}' not recognised; ignored.")
                else:
                    indices.append(match)

        # drop duplicates while keeping order
        seen: set[int] = set()
        indices = [i for i in indices if not (i in seen or seen.add(i))]

        if not indices:
            output_fn("No valid selection made.")
            continue

        # Flush any stray buffered input (Windows quirk guard)
        try:
            sys.stdin.flush()
        except AttributeError:
            pass  # not all platforms supply flush()

        output_fn("\n")
        
        if space_separated:
            return tuple(indices)
        
        return indices[0]


def get_confirmation(
    prompt: str = "Are you sure? [y/n]: ",
    default: str = "n",
) -> bool:
    """
    Gets a confirmation from the user

    # This is the little guardian: it makes sure the user really means it before doing something dangerous (like deleting mods or their hopes).
    """
    (input_fn, output_fn) = IOProvider().get_io()

    while True:
        output_fn("\n")
        response = input_fn(prompt).strip().lower()
        if not response:
            response = default

        if response in ("y", "yes"):
            return True
        elif response in ("n", "no"):
            return False
        else:
            output_fn("Invalid input. Please enter 'y' or 'n'.")
